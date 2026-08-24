from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from copy import deepcopy
from hashlib import sha256
import json, os, random
from typing import Any
from backend.engine.autonomy import AutonomyEngine
from backend.engine.simulation_systems import PopulationSystem, EconomySystem, ProductionSystem, DiplomacySystem, ClimateSystem, GovernmentSystem
from backend.platform.validation import WorldAudit
UTC=timezone.utc
def now_iso(): return datetime.now(UTC).isoformat()
def clamp(v,lo=0,hi=100): return max(lo,min(hi,float(v)))
@dataclass
class Event: id:str; world_id:str; kind:str; at:str; payload:dict[str,Any]; causes:list[str]=field(default_factory=list); source:str='system'
@dataclass
class Entity:
 id:str; name:str; kind:str; world_id:str; attributes:dict[str,Any]=field(default_factory=dict); needs:dict[str,float]=field(default_factory=dict); goals:list[dict[str,Any]]=field(default_factory=list); relations:dict[str,float]=field(default_factory=dict); memory_ids:list[str]=field(default_factory=list); alive:bool=True
class ValidationError(ValueError): pass
class StateValidator:
 def validate_world(self,w):
  for k in ('id','nome','tipo'):
   if not w.get(k): raise ValidationError(f'Campo obrigatório ausente: {k}')
  if not isinstance(w.get('regras',{}),dict): raise ValidationError('world.regras deve ser objeto')
 def validate_entity(self,e):
  if not e.get('id') or not e.get('world_id'): raise ValidationError('Entidade sem id/world_id')
class CausalLedger:
 def __init__(self): self.events={}
 def append(self,e):
  if e.id in self.events: raise ValidationError(f'Evento duplicado: {e.id}')
  self.events[e.id]=e; return e
 def explain(self,eid):
  out=[]; seen=set()
  def walk(i):
   if i in seen or i not in self.events:return
   seen.add(i); e=self.events[i]
   for p in e.causes: walk(p)
   out.append(e)
  walk(eid); return out
class EventScheduler:
 def __init__(self): self.queue=[]
 def schedule(self,e): self.queue.append(e); self.queue.sort(key=lambda x:x.at)
 def due(self,at):
  ready=[e for e in self.queue if e.at<=at]; self.queue=[e for e in self.queue if e.at>at]; return ready
class NeedsEngine:
 def tick(self,e,hours,activity='repouso'):
  if not e.alive:return e.needs
  rate={'repouso':1,'trabalho':1.35,'combate':2.5,'viagem':1.8}.get(activity,1.2)
  for k in ('fome','sede','sono','estresse'): e.needs[k]=clamp(e.needs.get(k,0)+hours*2*rate)
  if activity=='repouso':e.needs['sono']=clamp(e.needs.get('sono',0)-hours*5)
  return e.needs
class EconomyEngine:
 def price(self,base,stock,demand,scarcity=1):
  import math
  return round(max(.01,float(base)*(1+.35*math.tanh((float(demand)/max(float(stock),.01)-1)*scarcity))),2)
 def transaction(self,buyer,seller,price,quantity=1):
  total=round(price*quantity,2)
  if quantity<=0 or buyer.get('money',0)<total or seller.get('stock',0)<quantity: raise ValidationError('Transação inválida')
  buyer['money']=round(buyer.get('money',0)-total,2); seller['money']=round(seller.get('money',0)+total,2); seller['stock']-=quantity
class CombatEngine:
 def attack(self,a,d,w,rng=None):
  rng=rng or random.Random()
  if not a.alive or not d.alive: raise ValidationError('Combatente incapacitado')
  score=clamp(a.attributes.get('forca',50))*.35+clamp(a.attributes.get('tecnica',20))*.45+float(w.get('alcance',1))*5+rng.uniform(-10,10)-clamp(a.attributes.get('fadiga_pct',0))*.2
  defense=clamp(d.attributes.get('defesa',50)); hit=score>=defense*.8; severity=max(0,(score-defense*.6)/100)*float(w.get('potencia',10)) if hit else 0
  return {'acertou':hit,'severidade':round(severity,3),'score':round(score,2)}
class PopulationEngine:
 def birth(self,p,count=1): p['nascimentos']=int(p.get('nascimentos',0))+max(0,count); p['total']=int(p.get('total',0))+max(0,count)
 def death(self,p,count=1): p['mortes']=int(p.get('mortes',0))+max(0,count); p['total']=max(0,int(p.get('total',0))-max(0,count))
class SnapshotManager:
 def __init__(self,root): self.root=root
 def save(self,wid,state,label='manual'):
  payload={'schema':1,'world_id':wid,'label':label,'created_at':now_iso(),'state':deepcopy(state)}; raw=json.dumps(payload,ensure_ascii=False,sort_keys=True).encode(); digest=sha256(raw).hexdigest(); payload['sha256']=digest
  d=os.path.join(self.root,'worlds',wid,'snapshots'); os.makedirs(d,exist_ok=True); path=os.path.join(d,digest[:16]+'.json')
  with open(path,'w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
  return {'id':digest[:16],'sha256':digest,'path':path,'created_at':payload['created_at']}
class RPGRuntime:
 def __init__(self,data_dir):
  self.data_dir=data_dir; self.validator=StateValidator(); self.audit=WorldAudit(); self.causal=CausalLedger(); self.scheduler=EventScheduler(); self.needs=NeedsEngine(); self.economy=EconomyEngine(); self.combat=CombatEngine(); self.population=PopulationEngine(); self.snapshots=SnapshotManager(data_dir); self.autonomy=AutonomyEngine(); self.population_system=PopulationSystem(); self.economy_system=EconomySystem(); self.production=ProductionSystem(); self.diplomacy=DiplomacySystem(); self.climate=ClimateSystem(); self.government=GovernmentSystem(); self.entities={}
 def register_entity(self,e): self.validator.validate_entity(asdict(e)); self.entities[e.id]=e; return e
 def sync_entities_from_world(self,w):
  wid=str(w['id'])
  for r in w.get('entidades',[]):
   if not isinstance(r,dict) or not r.get('id') or str(r.get('world_id',wid))!=wid:continue
   self.entities[str(r['id'])]=Entity(str(r['id']),str(r.get('name') or r.get('nome') or 'Sem nome'),str(r.get('kind') or r.get('tipo') or 'npc'),wid,dict(r.get('attributes') or r.get('atributos') or {}),dict(r.get('needs') or r.get('necessidades') or {}),list(r.get('goals') or r.get('objetivos') or []),dict(r.get('relations') or r.get('relacoes') or {}),list(r.get('memory_ids') or []),bool(r.get('alive',True)))
 def persist_entities_to_world(self,w): w['entidades']=[asdict(e) for e in self.entities.values() if e.world_id==str(w['id'])]
 def simulate(self,w,hours):
  self.sync_entities_from_world(w); result=self.advance(w,hours)
  for e in list(self.entities.values()):
   if e.world_id!=str(w['id']) or not e.alive:continue
   self.needs.tick(e,hours,str(e.attributes.get('atividade','repouso'))); e.attributes['horas_simuladas']=float(e.attributes.get('horas_simuladas',0))+hours; d=self.autonomy.decide(asdict(e)); e.attributes['decisao_atual']=d.action; e.attributes['decisao_motivo']=d.reason
  self.persist_entities_to_world(w); self._tick_world_systems(w,hours); result['entidades_simuladas']=sum(e.world_id==str(w['id']) for e in self.entities.values()); result['auditoria']=self.audit.validate(w); return result
 def _tick_world_systems(self,w,hours):
  self.climate.tick(w.setdefault('clima',{}),hours); self.population_system.tick(w.setdefault('populacao',{}),hours/8760); self.economy_system.tick(w.setdefault('economia',{}),hours/24)
  if isinstance(w.get('governo'),dict): self.government.budget(w['governo'])
 def register_event(self,e):return self.causal.append(e)
 def advance(self,w,hours):
  self.validator.validate_world(w)
  if hours<=0:raise ValidationError('O avanço temporal deve ser positivo')
  current=w.setdefault('tempo',{}).get('iso') or now_iso(); dt=datetime.fromisoformat(current.replace('Z','+00:00')); target=dt+timedelta(hours=hours); w['tempo']['iso']=target.isoformat(); w['tempo']['horas_decorridas']=float(w['tempo'].get('horas_decorridas',0))+hours; due=self.scheduler.due(target.isoformat()); return {'tempo':w['tempo'],'eventos':[asdict(x) for x in due]}
