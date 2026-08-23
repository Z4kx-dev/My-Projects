import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

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

app = Flask(__name__, static_folder=str(FRONTEND_DIR))
carmilla = Carmilla(str(WORLDS_DIR))

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama").lower()
WORLD_ID_RE = re.compile(r"^(?:(real|fantasia):)?(\d{3})$")
CHAT_ID_RE = re.compile(r"^\d{3}$")
CATEGORIES = ("personagem", "npcs", "politica", "economia", "diario", "eventos")

SYSTEM_PROMPT = """Você é a IA principal de um simulador de RPG persistente.
SIMULE, não conte uma história roteirizada. O mundo existe independentemente do jogador. O tempo é irreversível. Toda ação tem custo, risco e consequência. Recursos são finitos. NPCs possuem livre-arbítrio, memória, personalidade, rotina, objetivos e relações próprias; podem aprender, esquecer, envelhecer, adoecer e morrer. O jogador controla somente o próprio personagem.
Não use plot armor, deus ex machina ou favorecimento artificial. Considere atributos, habilidades, experiência, saúde, fadiga, fome, sede, sono, dor, equipamento, terreno, clima, moral, economia, política e circunstâncias. Combate e ferimentos devem obedecer causalidade física/biológica e persistir. Não invente fatos que contradigam o estado fornecido.
O estado e a memória fornecidos pelo sistema são a fonte de continuidade. Quando algo não estiver registrado, trate como desconhecido em vez de afirmar como fato.
""".strip()

MEMORY_PROMPT = """Você é o analisador de memória do RPG. Não continue a narrativa e não invente fatos.
Identifique somente alterações persistentes relevantes: personagem, NPCs, política, economia, diário, eventos, localização, itens, relações, condições, habilidades, tempo ou consequências.
Retorne SOMENTE JSON válido: {"updates":[{"file":"personagem/estado.json","changes":{"campo":"valor"}}]}
Use somente personagem, npcs, politica, economia, diario e eventos. Não use caminhos absolutos, .. ou arquivos não-JSON. Se não houver alteração: {"updates":[]}.""".strip()


def now():
    return datetime.now(timezone.utc).isoformat()


def parse_world_id(world_id):
    value = str(world_id or "").strip()
    match = WORLD_ID_RE.fullmatch(value)
    if not match:
        raise ValueError("ID de mundo inválido. Use 001 ou real:001/fantasia:001.")
    tipo, numero = match.groups()
    return value, tipo or "real", numero


def world_path(world_id):
    value, tipo, numero = parse_world_id(world_id)
    return WORLDS_DIR / numero if ":" not in value else WORLDS_DIR / tipo / numero


def normalize_chat_id(chat_id):
    value = str(chat_id or "").strip()
    if value.isdigit():
        value = value.zfill(3)
    if not CHAT_ID_RE.fullmatch(value):
        raise ValueError("ID de chat inválido.")
    return value


def chat_path(world_id, chat_id):
    return world_path(world_id) / "chat" / f"{normalize_chat_id(chat_id)}.json"


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp, path)


def ensure_world(world_id):
    value, _, _ = parse_world_id(world_id)
    root = world_path(value)
    root.mkdir(parents=True, exist_ok=True)
    for category in ("chat", *CATEGORIES, "historico"):
        (root / category).mkdir(parents=True, exist_ok=True)
    carmilla.ensure_world(value)
    return value


def world_metadata(world_id):
    value, tipo, numero = parse_world_id(world_id)
    root = world_path(value)
    metadata = read_json(root / "mundo.json", {}) or {}
    metadata.setdefault("id", value)
    metadata.setdefault("tipo", tipo)
    metadata.setdefault("numero", numero)
    metadata.setdefault("nome", f"Mundo {'Fantasia' if tipo == 'fantasia' else 'Real'} {numero}")
    return metadata


def discover_worlds():
    result = []
    if not WORLDS_DIR.exists():
        return result
    for child in sorted(WORLDS_DIR.iterdir()):
        if child.is_dir() and re.fullmatch(r"\d{3}", child.name):
            result.append(world_metadata(child.name))
    for tipo in ("real", "fantasia"):
        folder = WORLDS_DIR / tipo
        if not folder.is_dir():
            continue
        for child in sorted(folder.iterdir()):
            if child.is_dir() and re.fullmatch(r"\d{3}", child.name):
                result.append(world_metadata(f"{tipo}:{child.name}"))
    return sorted(result, key=lambda x: (x.get("tipo", "real"), x.get("numero", "999"), x["id"]))


def next_world_id(tipo):
    used = {w.get("numero") for w in discover_worlds() if w.get("tipo") == tipo}
    for n in range(1, 1000):
        number = f"{n:03d}"
        if number not in used:
            return f"{tipo}:{number}"
    raise RuntimeError("Não há IDs de mundo disponíveis.")


def list_chats(world_id):
    world_id = ensure_world(world_id)
    folder = world_path(world_id) / "chat"
    result = []
    for path in sorted(folder.glob("*.json")):
        if not CHAT_ID_RE.fullmatch(path.stem):
            continue
        data = read_json(path, {}) or {}
        result.append({"id": path.stem, "world_id": world_id, "nome": data.get("nome", f"Chat {path.stem}"), "criado_em": data.get("criado_em"), "atualizado_em": data.get("atualizado_em"), "mensagens": len(data.get("mensagens", []))})
    return result


def next_chat_id(world_id):
    ids = [int(c["id"]) for c in list_chats(world_id)]
    return f"{(max(ids) + 1 if ids else 1):03d}"


def create_chat(world_id, nome="Nova conversa"):
    world_id = ensure_world(world_id)
    chat_id = next_chat_id(world_id)
    data = {"id": chat_id, "world_id": world_id, "nome": nome, "criado_em": now(), "atualizado_em": now(), "mensagens": []}
    write_json(chat_path(world_id, chat_id), data)
    return data


def load_chat(world_id, chat_id):
    world_id = ensure_world(world_id)
    data = read_json(chat_path(world_id, chat_id))
    if data is None:
        raise FileNotFoundError("Chat não encontrado.")
    return data


def save_chat(world_id, chat_id, data):
    data["atualizado_em"] = now()
    write_json(chat_path(world_id, chat_id), data)


def add_message(world_id, chat_id, role, content):
    data = load_chat(world_id, chat_id)
    data.setdefault("mensagens", []).append({"role": role, "content": content, "timestamp": now()})
    save_chat(world_id, chat_id, data)


def read_world_document(world_id):
    root = world_path(world_id)
    numero = parse_world_id(world_id)[2]
    for path in (root / f"mundo{numero}.docx", root / "mundo.docx"):
        if path.exists() and Document is not None:
            try:
                doc = Document(path)
                return "\n".join(p.text for p in doc.paragraphs if p.text.strip())[:50000]
            except Exception as exc:
                print("DOCX:", repr(exc))
    return ""


def build_memory_context(world_id):
    snapshot = carmilla.get_memory(world_id)
    return json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))[:60000]


def make_messages(world_id, chat_id):
    chat = load_chat(world_id, chat_id)
    context = build_memory_context(world_id)
    world_doc = read_world_document(world_id)
    system = SYSTEM_PROMPT + "\n\nIDENTIDADE DO MUNDO:\n" + json.dumps(world_metadata(world_id), ensure_ascii=False) + "\n\nMEMÓRIA:\n" + context + "\n\nDOCUMENTO DO MUNDO:\n" + world_doc
    return [{"role": "system", "content": system}] + chat.get("mensagens", [])[-30:]


def ollama_ok():
    try:
        return requests.get(f"{OLLAMA_URL}/api/tags", timeout=5).ok
    except requests.RequestException:
        return False


def ollama_request(messages, stream=True):
    response = requests.post(f"{OLLAMA_URL}/api/chat", json={"model": OLLAMA_MODEL, "messages": messages, "stream": stream}, stream=stream, timeout=600)
    response.raise_for_status()
    return response


def extract_json(text):
    if not text:
        return None
    candidates = [text.strip(), re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)]
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


def analyze_and_persist(world_id, user_message, assistant_message):
    try:
        prompt = MEMORY_PROMPT + "\n\nWORLD_ID: " + world_id + "\n\nJOGADOR:\n" + user_message + "\n\nIA:\n" + assistant_message + "\n\nMEMÓRIA ATUAL:\n" + build_memory_context(world_id)
        response = ollama_request([{ "role": "system", "content": MEMORY_PROMPT }, { "role": "user", "content": prompt }], stream=False)
        payload = response.json()
        content = payload.get("message", {}).get("content", "")
        result = extract_json(content) or {"updates": []}
        valid, rejected = carmilla.validator.validate_updates(result.get("updates", []))
        applied = carmilla.memory.apply_updates(world_id, valid)
        return {"applied": applied, "rejected": rejected}
    except Exception as exc:
        print("MEMORY ERROR:", repr(exc))
        return {"applied": [], "error": str(exc)}


@app.get("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(str(FRONTEND_DIR), path)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "model_provider": MODEL_PROVIDER, "model": OLLAMA_MODEL, "ollama": ollama_ok(), "carmilla": carmilla.status()})


@app.get("/api/carmilla")
def api_carmilla():
    return jsonify(carmilla.status())


@app.get("/api/worlds")
def api_worlds():
    return jsonify({"mundos": discover_worlds()})


@app.post("/api/worlds")
def api_create_world():
    body = request.get_json(silent=True) or {}
    tipo = body.get("tipo", "real")
    if tipo not in ("real", "fantasia"):
        return jsonify({"error": "tipo deve ser real ou fantasia"}), 400
    world_id = next_world_id(tipo)
    ensure_world(world_id)
    metadata = world_metadata(world_id)
    write_json(world_path(world_id) / "mundo.json", metadata)
    chat = create_chat(world_id)
    return jsonify({"id": world_id, "nome": metadata["nome"], "tipo": tipo, "chat": chat}), 201


@app.get("/api/worlds/<path:world_id>")
def api_world(world_id):
    try:
        ensure_world(world_id)
        return jsonify(world_metadata(world_id))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/worlds/<path:world_id>/chats")
def api_chats(world_id):
    try:
        return jsonify({"chats": list_chats(world_id)})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/worlds/<path:world_id>/chats")
def api_create_chat(world_id):
    try:
        body = request.get_json(silent=True) or {}
        return jsonify({"chat": create_chat(world_id, str(body.get("nome") or "Nova conversa"))}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/worlds/<path:world_id>/chats/<chat_id>")
def api_get_chat(world_id, chat_id):
    try:
        return jsonify(load_chat(world_id, chat_id))
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"error": str(exc)}), 404


@app.get("/api/worlds/<path:world_id>/memory")
def api_memory(world_id):
    try:
        return jsonify({"world_id": world_id, "memory": carmilla.get_memory(world_id)})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/worlds/<path:world_id>/files")
def api_files(world_id):
    try:
        ensure_world(world_id)
        root = world_path(world_id)
        tree = []
        for category in (*CATEGORIES, "chat", "historico"):
            folder = root / category
            files = [str(p.relative_to(root)).replace(os.sep, "/") for p in sorted(folder.rglob("*")) if p.is_file()]
            tree.append({"name": category, "type": "folder", "files": files})
        return jsonify({"world_id": world_id, "tree": tree})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/chat")
def api_chat():
    body = request.get_json(silent=True) or {}
    world_id, chat_id, user_message = body.get("world_id"), body.get("chat_id"), str(body.get("message") or "").strip()
    if not world_id or not chat_id or not user_message:
        return jsonify({"error": "world_id, chat_id e message são obrigatórios."}), 400
    if MODEL_PROVIDER != "ollama":
        return jsonify({"error": "Provider não suportado nesta versão. Use MODEL_PROVIDER=ollama."}), 501
    try:
        ensure_world(world_id)
        load_chat(world_id, chat_id)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"error": str(exc)}), 404
    add_message(world_id, chat_id, "user", user_message)

    @stream_with_context
    def generate():
        full_response = ""
        try:
            if not ollama_ok():
                yield "[[STREAM_ERROR]]Ollama não está acessível em " + OLLAMA_URL
                return
            response = ollama_request(make_messages(world_id, chat_id), stream=True)
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = data.get("message", {}).get("content", "")
                if text:
                    full_response += text
                    yield text
                if data.get("done"):
                    break
            if full_response:
                add_message(world_id, chat_id, "assistant", full_response)
                print("CARMILLA:", analyze_and_persist(world_id, user_message, full_response))
        except Exception as exc:
            print("STREAM ERROR:", repr(exc))
            yield "[[STREAM_ERROR]]" + str(exc)

    return Response(generate(), mimetype="text/plain; charset=utf-8", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    WORLDS_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=os.getenv("FLASK_DEBUG", "1") == "1", threaded=True)
