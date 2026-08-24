from __future__ import annotations

from flask import Blueprint, jsonify, request
from dataclasses import asdict
import os
import uuid

from backend.platform.runtime import RPGRuntime, Entity, ValidationError
from backend.platform.rag import RAGStore
from backend.platform.ai_guard import Decision, DecisionGuard


def install(app, worlds, memories, store):
    bp = Blueprint("platform", __name__, url_prefix="/api/v2")
    runtime = RPGRuntime(os.getenv("RPG_DATA_DIR", "data"))
    rag = RAGStore()

    @bp.get("/status")
    def status():
        return jsonify({"ok": True, "arquitetura": "motor-estado-llm-memoria-tools", "entidades": len(runtime.entities), "fontes": len(rag.sources)})

    @bp.get("/worlds/<world_id>/state")
    def state(world_id):
        world = worlds.get(str(world_id).zfill(3))
        if not world:
            return jsonify({"error": "Mundo não encontrado"}), 404
        runtime.validator.validate_world(world)
        return jsonify({"world": world, "entities": [asdict(x) for x in runtime.entities.values() if x.world_id == world_id]})

    @bp.post("/worlds/<world_id>/advance")
    def advance(world_id):
        world = worlds.get(str(world_id).zfill(3))
        if not world:
            return jsonify({"error": "Mundo não encontrado"}), 404
        body = request.get_json(silent=True) or {}
        try:
            result = runtime.advance(world, float(body.get("hours", 1)))
            worlds.save(world)
            return jsonify(result)
        except (ValueError, ValidationError) as exc:
            return jsonify({"error": str(exc)}), 400

    @bp.post("/worlds/<world_id>/entities")
    def entity(world_id):
        body = request.get_json(silent=True) or {}
        entity_id = str(body.get("id") or uuid.uuid4().hex[:12])
        item = Entity(entity_id, str(body.get("name") or "Sem nome"), str(body.get("kind") or "npc"), str(world_id), body.get("attributes") or {}, body.get("needs") or {}, body.get("goals") or [], body.get("relations") or {}, body.get("memory_ids") or [])
        try:
            runtime.register_entity(item)
        except ValidationError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"entity": asdict(item)}), 201

    @bp.get("/worlds/<world_id>/rag/search")
    def rag_search(world_id):
        query = str(request.args.get("q", "")).strip()
        if not query:
            return jsonify({"error": "q obrigatório"}), 400
        return jsonify(rag.search(query, min(30, max(1, int(request.args.get("limit", 8))))))

    @bp.post("/worlds/<world_id>/rag/source")
    def rag_source(world_id):
        body = request.get_json(silent=True) or {}
        text = str(body.get("text") or "")
        if not text:
            return jsonify({"error": "text obrigatório"}), 400
        source_id = str(body.get("id") or uuid.uuid4().hex[:12])
        source = rag.add_source(source_id, str(body.get("title") or source_id), text, {"world_id": world_id})
        return jsonify({"source": source}), 201

    app.register_blueprint(bp)
    return runtime, rag
