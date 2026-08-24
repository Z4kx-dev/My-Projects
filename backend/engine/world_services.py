from __future__ import annotations
from typing import Any
from math import hypot

class MapSystem:
    def add_location(self, world: dict[str,Any], location_id: str, name: str, x: float, y: float, kind: str='local'):
        locations=world.setdefault('mapa',{}).setdefault('locais',{})
        locations[location_id]={'id':location_id,'nome':name,'x':float(x),'y':float(y),'tipo':kind}
        return locations[location_id]
    def distance(self, world, a: str, b: str) -> float:
        loc=world.get('mapa',{}).get('locais',{}); p,q=loc.get(a),loc.get(b)
        if not p or not q: raise KeyError('Local não encontrado')
        return round(hypot(float(p['x'])-float(q['x']),float(p['y'])-float(q['y'])),3)

class WorldManager:
    def normalize(self, world: dict[str,Any]) -> dict[str,Any]:
        world.setdefault('versao',1); world.setdefault('tempo',{}); world.setdefault('entidades',[]); world.setdefault('eventos',[]); world.setdefault('memorias',[]); world.setdefault('mapa',{'locais':{}}); world.setdefault('clima',{}); world.setdefault('populacao',{}); world.setdefault('economia',{}); world.setdefault('governo',{}); world.setdefault('regras',{}); return world
    def exportable(self, world: dict[str,Any]) -> dict[str,Any]:
        self.normalize(world); return world.copy()
