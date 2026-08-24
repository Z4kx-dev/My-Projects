from __future__ import annotations
from typing import Any

class WorldAudit:
    def validate(self, world: dict[str,Any]) -> list[str]:
        errors=[]
        if not world.get('id'): errors.append('mundo sem id')
        if not world.get('nome'): errors.append('mundo sem nome')
        entities=world.get('entidades') or []
        ids=set()
        for e in entities:
            eid=str(e.get('id',''))
            if not eid: errors.append('entidade sem id'); continue
            if eid in ids: errors.append(f'ID de entidade duplicado: {eid}')
            ids.add(eid)
            if str(e.get('world_id',world.get('id'))) != str(world.get('id')): errors.append(f'entidade fora do mundo: {eid}')
            for key,val in (e.get('needs') or {}).items():
                try:
                    if float(val)<0 or float(val)>100: errors.append(f'necessidade fora de faixa: {eid}.{key}')
                except (TypeError,ValueError): errors.append(f'necessidade inválida: {eid}.{key}')
        pop=(world.get('populacao') or {}).get('total')
        if pop is not None and int(pop)<0: errors.append('população negativa')
        return errors

    def assert_valid(self, world):
        errors=self.validate(world)
        if errors: raise ValueError('; '.join(errors))
        return True
