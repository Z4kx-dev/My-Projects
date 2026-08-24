from __future__ import annotations
from typing import Any
from .registry import ToolRegistry
from backend.engine.simulator import SimulationEngine
from backend.memory.store import MemoryStore

def register_builtin(registry: ToolRegistry, world_getter, world_saver, memories: MemoryStore) -> None:
    def world_state(world_id: str) -> dict[str, Any]:
        world=world_getter(world_id); return {'id':world.get('id'),'nome':world.get('nome'),'tipo':world.get('tipo'),'tempo':world.get('tempo',{}),'entidades':world.get('entidades',[]),'populacao':world.get('populacao',{}),'economia':world.get('economia',{}),'clima':world.get('clima',{})}
    registry.register('consultar_mundo','Consulta o estado atual sem alterá-lo.',{'type':'object','properties':{'world_id':{'type':'string'}},'required':['world_id']},world_state)
    def advance_time(world_id: str, seconds: int, reason: str='ação') -> dict[str,Any]:
        if seconds<=0: raise ValueError('seconds deve ser positivo')
        world=world_getter(world_id); result=SimulationEngine(world).advance(int(seconds),reason); world_saver(result); return {'tempo':result['tempo'],'versao':result['versao']}
    registry.register('avancar_tempo','Avança o relógio do mundo sem retroceder.',{'type':'object','properties':{'world_id':{'type':'string'},'seconds':{'type':'integer','minimum':1},'reason':{'type':'string'}},'required':['world_id','seconds']},advance_time)
    registry.register('registrar_memoria','Persiste um fato relevante no mundo.',{'type':'object','properties':{'world_id':{'type':'string'},'content':{'type':'string'},'importance':{'type':'number','minimum':0,'maximum':1}},'required':['world_id','content']},lambda world_id,content,importance=.5: memories.add(world_id,content,importancia=importance))
    registry.register('buscar_memoria','Busca memórias relevantes.',{'type':'object','properties':{'world_id':{'type':'string'},'query':{'type':'string'},'limit':{'type':'integer','minimum':1,'maximum':50}},'required':['world_id','query']},lambda world_id,query,limit=12: memories.search(world_id,query,limit))
