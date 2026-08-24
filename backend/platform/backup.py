from __future__ import annotations
import json, os, shutil
from datetime import datetime, timezone
from hashlib import sha256

class BackupManager:
    def __init__(self, data_dir: str): self.data_dir=data_dir
    def backup_world(self, world_id: str) -> dict:
        src=os.path.join(self.data_dir,'worlds',world_id)
        if not os.path.isdir(src): raise FileNotFoundError('Mundo não encontrado')
        root=os.path.join(self.data_dir,'backups',world_id); os.makedirs(root,exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); dst=os.path.join(root,stamp); shutil.copytree(src,dst)
        manifest=[]
        for base,_,files in os.walk(dst):
            for name in files:
                p=os.path.join(base,name); h=sha256(open(p,'rb').read()).hexdigest(); manifest.append({'path':os.path.relpath(p,dst),'sha256':h})
        with open(os.path.join(dst,'manifest.json'),'w',encoding='utf-8') as f: json.dump({'world_id':world_id,'created_at':stamp,'files':manifest},f,ensure_ascii=False,indent=2)
        return {'world_id':world_id,'id':stamp,'path':dst,'arquivos':len(manifest)}
    def list(self, world_id: str):
        root=os.path.join(self.data_dir,'backups',world_id)
        return sorted(os.listdir(root)) if os.path.isdir(root) else []
