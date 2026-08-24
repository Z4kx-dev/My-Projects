from __future__ import annotations

from typing import Any
from .registry import ToolRegistry
from backend.engine.simulator import SimulationEngine
from backend.memory.store import MemoryStore


def register_builtin(registry: ToolRegistry, world_getter, world_saver, memories: MemoryStore) -> None:
    def advance_time(world_id: str, seconds: int, reason: str = "ação") -> dict[str, Any]:
        world = world_getter(world_id)
        engine = SimulationEngine(world)
        result = engine.advance(int(seconds), reason)
        world_saver(result)
        return {"tempo": result["tempo"], "versao": result["versao"]}

    registry.register("avancar_tempo", "Avança o relógio do mundo sem retroceder.", {"type": "object", "properties": {"world_id": {"type": "string"}, "seconds": {"type": "integer", "minimum": 0}, "reason": {"type": "string"}}, "required": ["world_id", "seconds"]}, advance_time)

    registry.register("registrar_memoria", "Persiste um fato relevante no mundo.", {"type": "object", "properties": {"world_id": {"type": "string"}, "content": {"type": "string"}, "importance": {"type": "number", "minimum": 0, "maximum": 1}}, "required": ["world_id", "content"]}, lambda world_id, content, importance=0.5: memories.add(world_id, content, importancia=importance))

    registry.register("buscar_memoria", "Busca memórias relevantes sem alterar o mundo.", {"type": "object", "properties": {"world_id": {"type": "string"}, "query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}}, "required": ["world_id", "query"]}, lambda world_id, query, limit=12: memories.search(world_id, query, limit))
