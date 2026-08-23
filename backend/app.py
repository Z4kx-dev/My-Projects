from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context

try:
    from docx import Document
except ImportError:
    Document = None

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
WORLDS_DIR = DATA_DIR / "mundos"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from guardian import Carmilla

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

CATEGORIES = ("personagem", "npcs", "politica", "economia", "diario", "eventos")
WORLD_RE = re.compile(r"^(?:(real|fantasia):)?(\d{3})$")
CHAT_RE = re.compile(r"^\d{3}$")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "900"))

carmilla = Carmilla(str(WORLDS_DIR))

SYSTEM_PROMPT = """Você é a IA principal de um simulador de RPG persistente.
SIMULE, não escreva uma história roteirizada. O mundo existe independentemente do jogador e o tempo é irreversível. Toda ação tem custo, risco e consequência. Recursos são finitos.
O jogador controla somente seu personagem. NPCs têm livre-arbítrio, memória, personalidade, rotina, objetivos, relações, capacidade de aprender e esquecer, envelhecer, adoecer e morrer.
Não use plot armor, deus ex machina ou favorecimento artificial. Considere atributos, habilidades, experiência, saúde, fadiga, fome, sede, sono, dor, equipamento, terreno, clima, moral, economia, política e circunstâncias.
Combate, ferimentos e morte devem obedecer causalidade física/biológica e consequências persistentes.
O estado e a memória fornecidos pelo sistema são a fonte de continuidade. Se algo não estiver registrado, trate como desconhecido. Não invente fatos para preencher lacunas.
""".strip()

MEMORY_PROMPT = """Você é o guardião de memória de um RPG persistente.
Analise a interação e registre SOMENTE fatos que realmente precisam sobreviver para o futuro. Não escreva narrativa.
Retorne somente JSON válido no formato:
{"updates":[{"file":"categoria/arquivo.json","changes":{"campo":"valor"}}]}
Categorias permitidas: personagem, npcs, politica, economia, diario, eventos.
Não use caminhos absolutos, .., arquivos fora dessas categorias ou markdown. Se não houver alteração persistente, retorne {"updates":[]}.
""".strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_world_id(world_id: str) -> tuple[str, str, str]:
    value = str(world_id or "").strip().lower()
    match = WORLD_RE.fullmatch(value)
    if not match:
        raise ValueError("ID de mundo inválido. Use 001, real:001 ou fantasia:001.")
    kind = match.group(1) or "real"
    number = match.group(2)
    return value, kind, number


def world_dir(world_id: str) -> Path:
    value, kind, number = parse_world_id(world_id)
    return WORLDS_DIR / number if ":" not in value else WORLDS_DIR / kind / number


def normalize_chat_id(chat_id: str) -> str:
    value = str(chat_id or "").strip()
    if value.isdigit():
        value = value.zfill(3)
    if not CHAT_RE.fullmatch(value):
        raise ValueError("ID de chat inválido.")
    return value


def chat_file(world_id: str, chat_id: str) -> Path:
    return world_dir(world_id) / "chat" / f"{normalize_chat_id(chat_id)}.json"


def read_json(path: Path, default: Any = None) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(temporary, path)


def ensure_world(world_id: str) -> str:
    value, _, _ = parse_world_id(world_id)
    root = world_dir(value)
    root.mkdir(parents=True, exist_ok=True)
    for folder in ("chat", "historico", *CATEGORIES):
        (root / folder).mkdir(parents=True, exist_ok=True)
    carmilla.ensure_world(value)
    metadata = root / "mundo.json"
    if not metadata.exists():
        _, kind, number = parse_world_id(value)
        write_json(metadata, {
            "id": value,
            "tipo": kind,
            "numero": number,
            "nome": f"Mundo {'Fantasia' if kind == 'fantasia' else 'Real'} {number}",
            "criado_em": utc_now(),
        })
    return value


def world_metadata(world_id: str) -> dict[str, Any]:
    value, kind, number = parse_world_id(world_id)
    root = world_dir(value)
    data = read_json(root / "mundo.json", {}) or {}
    data.setdefault("id", value)
    data.setdefault("tipo", kind)
    data.setdefault("numero", number)
    data.setdefault("nome", f"Mundo {'Fantasia' if kind == 'fantasia' else 'Real'} {number}")
    return data


def discover_worlds() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not WORLDS_DIR.exists():
        return result
    for child in sorted(WORLDS_DIR.iterdir()):
        if child.is_dir() and re.fullmatch(r"\d{3}", child.name):
            result.append(world_metadata(child.name))
    for kind in ("real", "fantasia"):
        folder = WORLDS_DIR / kind
        if not folder.is_dir():
            continue
        for child in sorted(folder.iterdir()):
            if child.is_dir() and re.fullmatch(r"\d{3}", child.name):
                result.append(world_metadata(f"{kind}:{child.name}"))
    return sorted(result, key=lambda item: (item.get("tipo", "real"), item.get("numero", "999"), item["id"]))


def next_world_id(kind: str) -> str:
    if kind not in {"real", "fantasia"}:
        raise ValueError("Tipo de mundo inválido.")
    used = {item.get("numero") for item in discover_worlds() if item.get("tipo") == kind}
    for number in range(1, 1000):
        candidate = f"{number:03d}"
        if candidate not in used:
            return candidate if kind == "real" else f"fantasia:{candidate}"
    raise RuntimeError("Não há IDs disponíveis.")


def list_chats(world_id: str) -> list[dict[str, Any]]:
    world_id = ensure_world(world_id)
    folder = world_dir(world_id) / "chat"
    chats = []
    for path in sorted(folder.glob("*.json")):
        if not CHAT_RE.fullmatch(path.stem):
            continue
        data = read_json(path, {}) or {}
        chats.append({
            "id": path.stem,
            "world_id": world_id,
            "nome": data.get("nome") or f"Chat {path.stem}",
            "criado_em": data.get("criado_em"),
            "atualizado_em": data.get("atualizado_em"),
            "mensagens": len(data.get("mensagens", [])),
        })
    return chats


def next_chat_id(world_id: str) -> str:
    ids = [int(item["id"]) for item in list_chats(world_id)]
    return f"{(max(ids) + 1 if ids else 1):03d}"


def create_chat(world_id: str, name: str = "Nova conversa") -> dict[str, Any]:
    world_id = ensure_world(world_id)
    chat_id = next_chat_id(world_id)
    data = {
        "id": chat_id,
        "world_id": world_id,
        "nome": name.strip()[:100] or "Nova conversa",
        "criado_em": utc_now(),
        "atualizado_em": utc_now(),
        "mensagens": [],
    }
    write_json(chat_file(world_id, chat_id), data)
    return data


def load_chat(world_id: str, chat_id: str) -> dict[str, Any]:
    world_id = ensure_world(world_id)
    data = read_json(chat_file(world_id, chat_id))
    if data is None:
        raise FileNotFoundError("Chat não encontrado.")
    return data


def save_chat(world_id: str, chat_id: str, data: dict[str, Any]) -> None:
    data["atualizado_em"] = utc_now()
    write_json(chat_file(world_id, chat_id), data)


def append_message(world_id: str, chat_id: str, role: str, content: str) -> None:
    chat = load_chat(world_id, chat_id)
    chat.setdefault("mensagens", []).append({"role": role, "content": content, "timestamp": utc_now()})
    save_chat(world_id, chat_id, chat)


def read_world_document(world_id: str) -> str:
    if Document is None:
        return ""
    root = world_dir(world_id)
    number = parse_world_id(world_id)[2]
    for path in (root / f"mundo{number}.docx", root / "mundo.docx"):
        if path.exists():
            try:
                document = Document(str(path))
                return "\n".join(p.text for p in document.paragraphs if p.text.strip())[:50000]
            except Exception as exc:
                app.logger.warning("Falha lendo DOCX %s: %r", path, exc)
    return ""


def memory_snapshot(world_id: str) -> dict[str, Any]:
    return carmilla.get_memory(ensure_world(world_id))


def build_context(world_id: str, chat_id: str) -> list[dict[str, str]]:
    chat = load_chat(world_id, chat_id)
    metadata = world_metadata(world_id)
    memory = memory_snapshot(world_id)
    document = read_world_document(world_id)
    system = SYSTEM_PROMPT + "\n\nMETADADOS DO MUNDO:\n" + json.dumps(metadata, ensure_ascii=False) + "\n\nMEMÓRIA E ESTADO PERSISTENTE:\n" + json.dumps(memory, ensure_ascii=False)[:60000]
    if document:
        system += "\n\nDOCUMENTO CANÔNICO DO MUNDO:\n" + document
    return [{"role": "system", "content": system}] + chat.get("mensagens", [])[-40:]


def ollama_tags() -> tuple[bool, list[str]]:
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        return True, [item.get("name", "") for item in response.json().get("models", [])]
    except (requests.RequestException, ValueError, AttributeError):
        return False, []


def ollama_stream(messages: list[dict[str, str]]):
    response = requests.post(f"{OLLAMA_URL}/api/chat", json={"model": OLLAMA_MODEL, "messages": messages, "stream": True}, stream=True, timeout=OLLAMA_TIMEOUT)
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        payload = json.loads(line)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        text = payload.get("message", {}).get("content", "")
        if text:
            yield text
        if payload.get("done"):
            break


def ollama_complete(messages: list[dict[str, str]]) -> str:
    response = requests.post(f"{OLLAMA_URL}/api/chat", json={"model": OLLAMA_MODEL, "messages": messages, "stream": False}, timeout=OLLAMA_TIMEOUT)
    response.raise_for_status()
    return response.json().get("message", {}).get("content", "")


def extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    candidates = [text.strip(), re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)]
    for candidate in candidates:
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(text[start:end + 1])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def persist_memory(world_id: str, user_message: str, assistant_message: str) -> None:
    try:
        prompt = (
            MEMORY_PROMPT
            + "\n\nWORLD_ID: " + world_id
            + "\n\nJOGADOR:\n" + user_message
            + "\n\nIA:\n" + assistant_message
            + "\n\nMEMÓRIA ATUAL:\n" + json.dumps(memory_snapshot(world_id), ensure_ascii=False)[:50000]
        )
        content = ollama_complete([{"role": "system", "content": MEMORY_PROMPT}, {"role": "user", "content": prompt}])
        result = extract_json(content) or {"updates": []}
        valid, rejected = carmilla.validator.validate_updates(result.get("updates", []))
        applied = carmilla.memory.apply_updates(world_id, valid)
        if rejected:
            app.logger.info("Carmilla rejeitou %d alterações inseguras", len(rejected))
        app.logger.info("Carmilla aplicou: %s", applied)
    except Exception as exc:
        app.logger.warning("Memória automática falhou: %r", exc)


@app.get("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.get("/<path:path>")
def frontend_file(path: str):
    return send_from_directory(str(FRONTEND_DIR), path)


@app.get("/api/health")
def health():
    connected, models = ollama_tags()
    return jsonify({"ok": True, "ollama": connected, "model": OLLAMA_MODEL, "models": models, "carmilla": carmilla.status()})


@app.get("/api/carmilla")
def api_carmilla():
    return jsonify(carmilla.status())


@app.get("/api/worlds")
def api_worlds():
    return jsonify({"mundos": discover_worlds()})


@app.post("/api/worlds")
def api_create_world():
    body = request.get_json(silent=True) or {}
    kind = str(body.get("tipo") or "real").lower()
    try:
        world_id = next_world_id(kind)
        ensure_world(world_id)
        metadata = world_metadata(world_id)
        if body.get("nome"):
            metadata["nome"] = str(body["nome"])[:100]
            write_json(world_dir(world_id) / "mundo.json", metadata)
        chat = create_chat(world_id)
        return jsonify({"world": metadata, "chat": chat}), 201
    except (ValueError, RuntimeError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/worlds/<path:world_id>")
def api_world(world_id: str):
    try:
        ensure_world(world_id)
        return jsonify(world_metadata(world_id))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/worlds/<path:world_id>/chats")
def api_chats(world_id: str):
    try:
        return jsonify({"chats": list_chats(world_id)})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/worlds/<path:world_id>/chats")
def api_create_chat(world_id: str):
    try:
        body = request.get_json(silent=True) or {}
        return jsonify({"chat": create_chat(world_id, str(body.get("nome") or "Nova conversa"))}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/worlds/<path:world_id>/chats/<chat_id>")
def api_get_chat(world_id: str, chat_id: str):
    try:
        return jsonify(load_chat(world_id, chat_id))
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"error": str(exc)}), 404


@app.get("/api/worlds/<path:world_id>/memory")
def api_memory(world_id: str):
    try:
        return jsonify({"world_id": world_id, "memory": memory_snapshot(world_id)})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/worlds/<path:world_id>/files")
def api_files(world_id: str):
    try:
        ensure_world(world_id)
        root = world_dir(world_id)
        tree = []
        for category in (*CATEGORIES, "chat", "historico"):
            folder = root / category
            files = [str(path.relative_to(root)).replace(os.sep, "/") for path in sorted(folder.rglob("*")) if path.is_file() and not path.name.endswith(".tmp")]
            tree.append({"name": category, "type": "folder", "files": files})
        tree.append({"name": "documentos", "type": "folder", "files": [path.name for path in root.glob("*.docx")]})
        return jsonify({"world_id": world_id, "tree": tree})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/chat")
def api_chat():
    body = request.get_json(silent=True) or {}
    world_id = str(body.get("world_id") or "").strip()
    chat_id = str(body.get("chat_id") or "").strip()
    user_message = str(body.get("message") or "").strip()
    if not world_id or not chat_id or not user_message:
        return jsonify({"error": "world_id, chat_id e message são obrigatórios."}), 400
    try:
        ensure_world(world_id)
        normalize_chat_id(chat_id)
        load_chat(world_id, chat_id)
        append_message(world_id, chat_id, "user", user_message)
        messages = build_context(world_id, chat_id)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"error": str(exc)}), 400

    @stream_with_context
    def generate():
        full_response = ""
        try:
            for chunk in ollama_stream(messages):
                full_response += chunk
                yield chunk
            append_message(world_id, chat_id, "assistant", full_response)
            persist_memory(world_id, user_message, full_response)
        except Exception as exc:
            app.logger.exception("Falha no streaming")
            yield "\n\n[[STREAM_ERROR]]" + str(exc)

    return Response(generate(), mimetype="text/plain; charset=utf-8", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "X-Accel-Buffering": "no", "X-RPG-World": world_id, "X-RPG-Chat": normalize_chat_id(chat_id)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "1") == "1", threaded=True)
