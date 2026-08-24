from __future__ import annotations

from typing import Any


class SocietyEngine:
    def __init__(self, world: dict[str, Any]):
        self.world = world
        self.world.setdefault("sociedade", {})
        self.world["sociedade"].setdefault("instituicoes", {})
        self.world["sociedade"].setdefault("grupos", {})

    def relation(self, entity_a: dict[str, Any], entity_b_id: str, delta: float) -> float:
        relations = entity_a.setdefault("relacoes", {})
        value = max(-100.0, min(100.0, float(relations.get(entity_b_id, 0)) + float(delta)))
        relations[entity_b_id] = value
        return value

    def create_group(self, group_id: str, name: str, members: list[str] | None = None) -> dict[str, Any]:
        if group_id in self.world["sociedade"]["grupos"]:
            raise ValueError("Grupo já existe")
        group = {"id": group_id, "nome": name, "membros": members or [], "objetivos": [], "recursos": {}}
        self.world["sociedade"]["grupos"][group_id] = group
        return group
