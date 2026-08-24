from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR in sys.path:
    sys.path.remove(SCRIPT_DIR)
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import json
import re
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context

FRONT = os.path.join(BASE, "frontend")
DATA = os.path.abspath(os.getenv("RPG_DATA_DIR", os.path.join(BASE, "data")))

from backend.core.storage import JsonStore
from backend.core.repository import WorldRepository, ChatRepository
from backend.memory.store import MemoryStore
from backend.memory.context import ContextBuilder
from backend.memory.retrieval import HybridRetriever
from backend.ai.client import OllamaClient, LLMError
from backend.ai.orchestrator import RPGOrchestrator
from backend.ai.agent import RPGAgent
from backend.tools.registry import ToolRegistry
from backend.tools.builtin import register_builtin

app = Flask(__name__, static_folder=FRONT, static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("RPG_MAX_REQUEST_BYTES", str(2 * 1024 * 1024)))
store = JsonStore(DATA)
worlds = WorldRepository(store)
chats = ChatRepository(store, worlds)
memories = MemoryStore(store)
retriever = HybridRetriever(memories)
context = ContextBuilder(worlds, chats, memories, max_chars=max(10000, int(os.getenv("RPG_CONTEXT_MAX_CHARS", "120000"))))
llm = OllamaClient()
orchestrator = RPGOrchestrator(llm, context)
tools = ToolRegistry()
register_builtin(tools, lambda wid: worlds.get(wid) or worlds.ensure(wid), worlds.save, memories)


def normalize_id(value: object) -> str:
    value = str(value or "").strip()
    value = value.zfill(3) if value.isdigit() else value
    if not re.fullmatch(r"\d{3}", value):
        raise ValueError("ID inválido; use três dígitos.")
    return value


def next_id(existing: list[str]) -> str:
    nums = [int(x) for x in existing if str(x).isdigit()]
    return f"{max(nums, default=0) + 1:03d}"


def body_options(body: dict) -> dict | None:
    value = body.get("options")
    return value if isinstance(value, dict) else None


@app.get("/")
def index():
    return send_from_directory(FRONT, "index.html")


@app.get("/api/health")
def health():
    try:
        import requests
        r = requests.get(f"{llm.url}/api/tags", timeout=3)
        models = r.json().get("models", []) if r.ok else []
        status = 200 if r.ok else 503
        return jsonify({"ok": r.ok, "ollama": r.ok, "model": llm.model, "models": [m.get("name") for m in models]}), status
    except Exception as exc:
        return jsonify({"ok": False, "ollama": False, "model": llm.model, "models": [], "erro": str(exc)}), 503


@app.get("/api/worlds")
def list_worlds():
    result = []
    for world in worlds.list():
        wid = normalize_id(world["id"])
        result.append({**world, "id": wid, "chats": chats.list(wid)})
    return jsonify({"mundos": result})


@app.post("/api/worlds")
def create_world():
    body = request.get_json(silent=True) or {}
    current = [str(w["id"]) for w in worlds.list()]
    wid = next_id(current)
    tipo = "fantasia" if str(body.get("tipo", "real")).lower() == "fantasia" else "real"
    world = worlds.ensure(wid, str(body.get("nome") or f"Mundo {wid}").strip(), tipo)
    world["descricao"] = str(body.get("descricao") or "")
    world["regras"] = body.get("regras") if isinstance(body.get("regras"), dict) else {}
    worlds.save(world)
    return jsonify({"mundo": {**world, "id": wid, "chats": []}}), 201


@app.get("/api/worlds/<world_id>")
def get_world(world_id):
    wid = normalize_id(world_id)
    world = worlds.get(wid)
    if not world:
        return jsonify({"error": "Mundo não encontrado."}), 404
    return jsonify({"mundo": {**world, "id": wid, "chats": chats.list(wid)}})


@app.get("/api/worlds/<world_id>/chats")
def list_chats(world_id):
    return jsonify({"chats": chats.list(normalize_id(world_id))})


@app.post("/api/worlds/<world_id>/chats")
def create_chat(world_id):
    wid = normalize_id(world_id)
    if not worlds.get(wid):
        return jsonify({"error": "Mundo não encontrado."}), 404
    cid = next_id([str(x["id"]) for x in chats.list(wid)])
    body = request.get_json(silent=True) or {}
    chat = chats.create(wid, cid, str(body.get("nome") or "Nova conversa").strip() or "Nova conversa")
    return jsonify({"chat": chat}), 201


@app.get("/api/worlds/<world_id>/chats/<chat_id>")
def get_chat(world_id, chat_id):
    chat = chats.get(normalize_id(world_id), normalize_id(chat_id))
    if not chat:
        return jsonify({"error": "Chat não encontrado."}), 404
    return jsonify(chat)


@app.delete("/api/worlds/<world_id>/chats/<chat_id>")
def delete_chat(world_id, chat_id):
    wid, cid = normalize_id(world_id), normalize_id(chat_id)
    if not chats.get(wid, cid):
        return jsonify({"error": "Chat não encontrado."}), 404
    store.delete(*chats.new_parts(wid, cid))
    store.delete(*chats.legacy_parts(wid, cid))
    return jsonify({"ok": True})


@app.get("/api/worlds/<world_id>/memory")
def list_memory(world_id):
    return jsonify({"memorias": memories.list(normalize_id(world_id))})


@app.get("/api/worlds/<world_id>/memory/search")
def search_memory(world_id):
    query = str(request.args.get("q", "")).strip()
    if not query:
        return jsonify({"error": "Informe q."}), 400
    try:
        limit = min(50, max(1, int(request.args.get("limit", 12))))
    except ValueError:
        return jsonify({"error": "limit inválido."}), 400
    return jsonify({"memorias": retriever.search(normalize_id(world_id), query, limit)})


@app.post("/api/worlds/<world_id>/memory")
def create_memory(world_id):
    body = request.get_json(silent=True) or {}
    try:
        item = memories.add(normalize_id(world_id), str(body.get("conteudo") or body.get("content") or ""), str(body.get("tipo") or "fato"), float(body.get("importancia", 0.5)), body.get("tags") or [], "usuario")
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"memoria": item}), 201


@app.get("/api/tools")
def list_tools():
    return jsonify({"ferramentas": tools.definitions()})


@app.post("/api/tools/<name>")
def call_tool(name):
    body = request.get_json(silent=True) or {}
    try:
        return jsonify({"resultado": tools.call(name, body)})
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


def validate_chat_request(body: dict) -> tuple[str, str, str]:
    wid, cid = normalize_id(body.get("world_id")), normalize_id(body.get("chat_id"))
    text = str(body.get("message") or "").strip()
    if not text:
        raise ValueError("Mensagem vazia.")
    if len(text) > int(os.getenv("RPG_MAX_MESSAGE_CHARS", "30000")):
        raise ValueError("Mensagem excede o limite permitido.")
    if not worlds.get(wid) or not chats.get(wid, cid):
        raise LookupError("Mundo ou chat não encontrado.")
    return wid, cid, text


@app.post("/api/chat")
def chat_api():
    body = request.get_json(silent=True) or {}
    try:
        wid, cid, text = validate_chat_request(body)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404

    chats.append(wid, cid, "user", text)

    def stream():
        full: list[str] = []
        try:
            # O chat principal usa o mesmo motor de contexto/agent do endpoint avançado.
            result = RPGAgent(llm, orchestrator, tools, max_iterations=min(10, max(1, int(body.get("max_iterations", 6))))).run(wid, cid, text, body_options(body))
            answer = result.answer.strip()
            if answer:
                chats.append(wid, cid, "assistant", answer)
                memories.add(wid, answer, "resposta", 0.15, ["chat", "agente"], "ia")
            yield "data: " + json.dumps({"token": answer, "tool_calls": result.tool_calls, "tool_results": result.tool_results, "iteracoes": result.iterations}, ensure_ascii=False, default=str) + "\n\n"
            yield "data: [DONE]\n\n"
        except LLMError as exc:
            yield "data: " + json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n\n"
        except Exception as exc:
            yield "data: " + json.dumps({"error": f"Erro interno: {exc}"}, ensure_ascii=False) + "\n\n"

    return Response(stream_with_context(stream()), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/agent")
def agent_api():
    body = request.get_json(silent=True) or {}
    try:
        wid, cid, text = validate_chat_request(body)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    try:
        result = RPGAgent(llm, orchestrator, tools, max_iterations=min(10, max(1, int(body.get("max_iterations", 6))))).run(wid, cid, text, body_options(body))
        chats.append(wid, cid, "user", text)
        if result.answer:
            chats.append(wid, cid, "assistant", result.answer)
            memories.add(wid, result.answer, "resposta", 0.2, ["agente", "chat"], "ia")
        return jsonify({"resposta": result.answer, "tool_calls": result.tool_calls, "tool_results": result.tool_results, "iteracoes": result.iterations})
    except LLMError as exc:
        return jsonify({"error": str(exc)}), 502


@app.errorhandler(Exception)
def handle_error(exc):
    return jsonify({"error": str(exc)}), 500


from backend.platform.api import install as install_platform
platform_runtime, notebook_provider = install_platform(app, worlds, memories, store)
context.rag_provider = lambda world_id, query: notebook_provider(world_id).context(query, 6)


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "5000")), debug=False, threaded=True)
