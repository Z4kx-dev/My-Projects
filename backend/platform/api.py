from __future__ import annotations
from dataclasses import asdict
import os, tempfile, uuid
from pathlib import Path
from flask import Blueprint, jsonify, request
from backend.platform.runtime import RPGRuntime, Entity, ValidationError
from backend.platform.backup import BackupManager
from backend.rag.notebook import NotebookWorkspace

def install(app, worlds, memories, store):
    bp=Blueprint('platform',__name__,url_prefix='/api/v2'); data_root=Path(os.getenv('RPG_DATA_DIR','data')); runtime=RPGRuntime(str(data_root)); backups=BackupManager(str(data_root)); notebooks={}
    def notebook(wid):
        wid=str(wid).zfill(3)
        if wid not in notebooks: notebooks[wid]=NotebookWorkspace(wid,data_root/'notebooks'/wid)
        return notebooks[wid]
    def world_or_404(wid):
        w=worlds.get(str(wid).zfill(3)); return w
    @bp.get('/status')
    def status(): return jsonify({'ok':True,'versao':'0.9.0','arquitetura':'estado->simulacao->memoria->rag->llm','entidades':len(runtime.entities),'notebooks':len(notebooks),'guard':True,'agente':True,'autonomia':True,'backup':True})
    @bp.get('/worlds/<world_id>/state')
    def state(world_id):
        wid=str(world_id).zfill(3); w=world_or_404(wid)
        if not w:return jsonify({'error':'Mundo não encontrado'}),404
        runtime.sync_entities_from_world(w); return jsonify({'world':w,'entities':[asdict(e) for e in runtime.entities.values() if e.world_id==wid]})
    @bp.post('/worlds/<world_id>/advance')
    def advance(world_id):
        wid=str(world_id).zfill(3); w=world_or_404(wid)
        if not w:return jsonify({'error':'Mundo não encontrado'}),404
        body=request.get_json(silent=True) or {}
        try:
            result=runtime.simulate(w,float(body.get('hours',1))); worlds.save(w); return jsonify(result)
        except (ValueError,ValidationError) as exc:return jsonify({'error':str(exc)}),400
    @bp.post('/worlds/<world_id>/snapshot')
    def snapshot(world_id):
        wid=str(world_id).zfill(3); w=world_or_404(wid)
        if not w:return jsonify({'error':'Mundo não encontrado'}),404
        runtime.sync_entities_from_world(w); runtime.persist_entities_to_world(w); worlds.save(w); body=request.get_json(silent=True) or {}
        return jsonify({'snapshot':runtime.snapshots.save(wid,w,str(body.get('label') or 'manual'))}),201
    @bp.post('/worlds/<world_id>/backup')
    def backup(world_id):
        wid=str(world_id).zfill(3)
        if not world_or_404(wid):return jsonify({'error':'Mundo não encontrado'}),404
        return jsonify({'backup':backups.backup_world(wid)}),201
    @bp.get('/worlds/<world_id>/backups')
    def list_backups(world_id): return jsonify({'backups':backups.list(str(world_id).zfill(3))})
    @bp.post('/worlds/<world_id>/entities')
    def entity(world_id):
        wid=str(world_id).zfill(3); w=world_or_404(wid)
        if not w:return jsonify({'error':'Mundo não encontrado'}),404
        b=request.get_json(silent=True) or {}; item=Entity(str(b.get('id') or uuid.uuid4().hex[:12]),str(b.get('name') or 'Sem nome'),str(b.get('kind') or 'npc'),wid,b.get('attributes') or {},b.get('needs') or {},b.get('goals') or [],b.get('relations') or {},b.get('memory_ids') or [])
        try: runtime.sync_entities_from_world(w); runtime.register_entity(item); runtime.persist_entities_to_world(w); worlds.save(w)
        except ValidationError as exc:return jsonify({'error':str(exc)}),400
        return jsonify({'entity':asdict(item)}),201
    @bp.get('/worlds/<world_id>/autonomy')
    def autonomy(world_id):
        wid=str(world_id).zfill(3); w=world_or_404(wid)
        if not w:return jsonify({'error':'Mundo não encontrado'}),404
        runtime.sync_entities_from_world(w); return jsonify({'decisoes':runtime.autonomy.plan([asdict(e) for e in runtime.entities.values() if e.world_id==wid])})
    @bp.post('/worlds/<world_id>/production')
    def production(world_id):
        w=world_or_404(world_id)
        if not w:return jsonify({'error':'Mundo não encontrado'}),404
        b=request.get_json(silent=True) or {}; stock=w.setdefault('economia',{}).setdefault('estoques',{})
        result=runtime.production.produce(stock,b.get('recipe') or {},int(b.get('workers',1)),float(b.get('periods',1))); worlds.save(w); return jsonify(result),200 if result.get('ok') else 409
    @bp.post('/worlds/<world_id>/economy/tick')
    def economy_tick(world_id):
        w=world_or_404(world_id)
        if not w:return jsonify({'error':'Mundo não encontrado'}),404
        w['economia']=runtime.economy_system.tick(w.setdefault('economia',{}),float((request.get_json(silent=True) or {}).get('periods',1))); worlds.save(w); return jsonify(w['economia'])
    @bp.post('/worlds/<world_id>/diplomacy')
    def diplomacy(world_id):
        b=request.get_json(silent=True) or {}; score=runtime.diplomacy.score(float(b.get('relacao',50)),float(b.get('poder_ratio',1)),float(b.get('confianca',50))); return jsonify({'score':round(score,2),'classificacao':runtime.diplomacy.classify(score)})
    @bp.post('/worlds/<world_id>/validate')
    def validate(world_id):
        w=world_or_404(world_id)
        if not w:return jsonify({'error':'Mundo não encontrado'}),404
        runtime.sync_entities_from_world(w); errors=runtime.audit.validate(w); return jsonify({'ok':not errors,'validado':not errors,'erros':errors,'entidades':sum(e.world_id==str(world_id).zfill(3) for e in runtime.entities.values())}),409 if errors else 200
    @bp.get('/worlds/<world_id>/rag/sources')
    def rag_sources(world_id):
        nb=notebook(world_id); return jsonify({'fontes':[{'id':d.source_id,'nome':d.name,'mime_type':d.mime_type,'metadata':d.metadata} for d in nb.documents.values()]})
    @bp.get('/worlds/<world_id>/rag/search')
    def rag_search(world_id):
        q=str(request.args.get('q','')).strip()
        if not q:return jsonify({'error':'q obrigatório'}),400
        return jsonify({'resultados':[asdict(x) for x in notebook(world_id).search(q,min(30,max(1,int(request.args.get('limit',8)))))]})
    @bp.get('/worlds/<world_id>/rag/context')
    def rag_context(world_id):
        q=str(request.args.get('q','')).strip()
        if not q:return jsonify({'error':'q obrigatório'}),400
        text,refs=notebook(world_id).context(q,min(12,max(1,int(request.args.get('limit',6))))); return jsonify({'contexto':text,'citacoes':[asdict(x) for x in refs]})
    @bp.post('/worlds/<world_id>/rag/source')
    def rag_source(world_id):
        b=request.get_json(silent=True) or {}; text=str(b.get('text') or '')
        if not text:return jsonify({'error':'text obrigatório'}),400
        d=notebook(world_id).add_text(str(b.get('title') or 'Fonte sem título'),text,str(b.get('mime_type') or 'text/plain'),{str(k):str(v) for k,v in (b.get('metadata') or {}).items()}); return jsonify({'source':asdict(d)}),201
    @bp.post('/worlds/<world_id>/rag/upload')
    def rag_upload(world_id):
        up=request.files.get('file')
        if up is None or not up.filename:return jsonify({'error':'Envie um arquivo no campo file.'}),400
        suffix=Path(up.filename).suffix.lower(); allowed={'.txt','.md','.markdown','.html','.htm','.json','.csv','.pdf','.docx'}
        if suffix not in allowed:return jsonify({'error':f'Formato não suportado: {suffix or "<sem extensão>"}.'}),415
        raw=up.read()
        if len(raw)>10*1024*1024:return jsonify({'error':'Arquivo excede 10 MB.'}),413
        try:
            if suffix in {'.pdf','.docx'}:
                with tempfile.NamedTemporaryFile(suffix=suffix,delete=False) as tmp: tmp.write(raw); path=Path(tmp.name)
                try:
                    d=notebook(world_id).ingestor.from_file(path,{'filename':up.filename}); notebook(world_id).documents[d.source_id]=d; notebook(world_id).index.upsert(notebook(world_id).ingestor.chunk(d)); notebook(world_id)._save_sources()
                finally:path.unlink(missing_ok=True)
            else:d=notebook(world_id).add_text(up.filename,raw.decode('utf-8'),up.mimetype or 'text/plain',{'filename':up.filename})
            return jsonify({'source':asdict(d)}),201
        except UnicodeDecodeError:return jsonify({'error':'Texto deve estar em UTF-8.'}),415
        except (ValueError,OSError) as exc:return jsonify({'error':str(exc)}),422
    app.register_blueprint(bp); return runtime,notebook
