from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
import tempfile
import uuid

from flask import Blueprint, jsonify, request

from backend.platform.runtime import RPGRuntime, Entity, ValidationError
from backend.rag.notebook import NotebookWorkspace


def install(app, worlds, memories, store):
    bp = Blueprint("platform", __name__, url_prefix="/api/v2")
    data_root = Path(os.getenv("RPG_DATA_DIR", "data"))
    runtime = RPGRuntime(str(data_root))
    notebooks: dict[str, NotebookWorkspace] = {}

    def notebook(world_id: str) -> NotebookWorkspace:
        wid = str(world_id).zfill(3)
        if wid not in notebooks:
            notebooks[wid] = NotebookWorkspace(wid, data_root / "notebooks" / wid)
        return notebooks[wid]

    @bp.get("/status")
    def status():
        return jsonify({"ok": True, "arquitetura": "motor-estado-llm-memoria-rag-tools", "entidades": len(runtime.entities), "notebooks": len(notebooks), "guard": True, "agente": True})

    @bp.get("/worlds/<world_id>/state")
    def state(world_id):
        wid = str(world_id).zfill(3)
        world = worlds.get(wid)
        if not world:
            return jsonify({"error": "Mundo não encontrado"}), 404
        runtime.sync_entities_from_world(world)
        runtime.validator.validate_world(world)
        return jsonify({"world": world, "entities": [asdict(x) for x in runtime.entities.values() if x.world_id == wid]})

    @bp.post("/worlds/<world_id>/advance")
    def advance(world_id):
        wid = str(world_id).zfill(3)
        world = worlds.get(wid)
        if not world:
            return jsonify({"error": "Mundo não encontrado"}), 404
        body = request.get_json(silent=True) or {}
        try:
            result = runtime.simulate(world, float(body.get("hours", 1)))
            worlds.save(world)
            return jsonify(result)
        except (ValueError, ValidationError) as exc:
            return jsonify({"error": str(exc)}), 400

    @bp.post("/worlds/<world_id>/snapshot")
    def snapshot(world_id):
        wid = str(world_id).zfill(3)
        world = worlds.get(wid)
        if not world:
            return jsonify({"error": "Mundo não encontrado"}), 404
        runtime.sync_entities_from_world(world)
        runtime.persist_entities_to_world(world)
        worlds.save(world)
        body = request.get_json(silent=True) or {}
        return jsonify({"snapshot": runtime.snapshots.save(wid, world, str(body.get("label") or "manual"))}), 201

    @bp.post("/worlds/<world_id>/entities")
    def entity(world_id):
        wid = str(world_id).zfill(3)
        world = worlds.get(wid)
        if not world:
            return jsonify({"error": "Mundo não encontrado"}), 404
        body = request.get_json(silent=True) or {}
        entity_id = str(body.get("id") or uuid.uuid4().hex[:12])
        item = Entity(entity_id, str(body.get("name") or "Sem nome"), str(body.get("kind") or "npc"), wid, body.get("attributes") or {}, body.get("needs") or {}, body.get("goals") or [], body.get("relations") or {}, body.get("memory_ids") or [])
        try:
            runtime.sync_entities_from_world(world)
            runtime.register_entity(item)
            runtime.persist_entities_to_world(world)
            worlds.save(world)
        except ValidationError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"entity": asdict(item)}), 201

    @bp.get("/worlds/<world_id>/rag/sources")
    def rag_sources(world_id):
        nb = notebook(world_id)
        return jsonify({"fontes": [{"id": d.source_id, "nome": d.name, "mime_type": d.mime_type, "metadata": d.metadata} for d in nb.documents.values()]})

    @bp.get("/worlds/<world_id>/rag/search")
    def rag_search(world_id):
        query = str(request.args.get("q", "")).strip()
        if not query:
            return jsonify({"error": "q obrigatório"}), 400
        limit = min(30, max(1, int(request.args.get("limit", 8))))
        return jsonify({"resultados": [asdict(x) for x in notebook(world_id).search(query, limit)]})

    @bp.get("/worlds/<world_id>/rag/context")
    def rag_context(world_id):
        query = str(request.args.get("q", "")).strip()
        if not query:
            return jsonify({"error": "q obrigatório"}), 400
        text, refs = notebook(world_id).context(query, min(12, max(1, int(request.args.get("limit", 6)))))
        return jsonify({"contexto": text, "citacoes": [asdict(x) for x in refs]})

    @bp.post("/worlds/<world_id>/rag/source")
    def rag_source(world_id):
        body = request.get_json(silent=True) or {}
        text = str(body.get("text") or "")
        if not text:
            return jsonify({"error": "text obrigatório"}), 400
        document = notebook(world_id).add_text(str(body.get("title") or "Fonte sem título"), text, str(body.get("mime_type") or "text/plain"), {str(k): str(v) for k, v in (body.get("metadata") or {}).items()})
        return jsonify({"source": asdict(document)}), 201

    @bp.post("/worlds/<world_id>/rag/upload")
    def rag_upload(world_id):
        uploaded = request.files.get("file")
        if uploaded is None or not uploaded.filename:
            return jsonify({"error": "Envie um arquivo no campo file."}), 400
        suffix = Path(uploaded.filename).suffix.lower()
        allowed = {".txt", ".md", ".markdown", ".html", ".htm", ".json", ".csv", ".pdf", ".docx"}
        if suffix not in allowed:
            return jsonify({"error": f"Formato não suportado: {suffix or '<sem extensão>'}."}), 415
        raw = uploaded.read()
        if len(raw) > 10 * 1024 * 1024:
            return jsonify({"error": "Arquivo excede o limite de 10 MB."}), 413
        try:
            if suffix in {".pdf", ".docx"}:
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(raw)
                    temp_path = Path(tmp.name)
                try:
                    document = notebook(world_id).ingestor.from_file(temp_path, {"filename": uploaded.filename})
                    notebook(world_id).documents[document.source_id] = document
                    notebook(world_id).index.upsert(notebook(world_id).ingestor.chunk(document))
                    notebook(world_id)._save_sources()
                finally:
                    temp_path.unlink(missing_ok=True)
            else:
                document = notebook(world_id).add_text(uploaded.filename, raw.decode("utf-8"), uploaded.mimetype or "text/plain", {"filename": uploaded.filename})
            return jsonify({"source": asdict(document)}), 201
        except UnicodeDecodeError:
            return jsonify({"error": "Arquivo de texto precisa estar em UTF-8."}), 415
        except (ValueError, OSError) as exc:
            return jsonify({"error": str(exc)}), 422

    @bp.post("/worlds/<world_id>/validate")
    def validate(world_id):
        wid = str(world_id).zfill(3)
        world = worlds.get(wid)
        if not world:
            return jsonify({"error": "Mundo não encontrado"}), 404
        try:
            runtime.sync_entities_from_world(world)
            runtime.validator.validate_world(world)
            for entity in runtime.entities.values():
                if entity.world_id == wid:
                    runtime.validator.validate_entity(asdict(entity))
            return jsonify({"ok": True, "validado": True, "entidades": sum(e.world_id == wid for e in runtime.entities.values())})
        except ValidationError as exc:
            return jsonify({"ok": False, "validado": False, "error": str(exc)}), 409

    @bp.get("/tools/guard")
    def guard_status():
        return jsonify({"enabled": True, "mutations_require_validation": True})

    app.register_blueprint(bp)
    return runtime, notebook
