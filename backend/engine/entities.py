from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any
from backend.core.models import utc_now


@dataclass
class Entity:
    id: str
    nome: str
    tipo: str
    atributos: dict[str, float] = field(default_factory=dict)
    estado: dict[str, Any] = field(default_factory=dict)
    relacoes: dict[str, float] = field(default_factory=dict)
    objetivos: list[str] = field(default_factory=list)
    rotina: list[dict[str, Any]] = field(default_factory=list)
    memoria_ids: list[str] = field(default_factory=list)
    criado_em: str = field(default_factory=utc_now)
    atualizado_em: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EntityManager:
    def __init__(self, world: dict[str, Any]):
        self.world = world
        self.world.setdefault("entidades", {})

    def create(self, entity: Entity) -> dict[str, Any]:
        if entity.id in self.world["entidades"]:
            raise ValueError("Entidade já existe")
        self.world["entidades"][entity.id] = entity.to_dict()
        return self.world["entidades"][entity.id]

    def get(self, entity_id: str) -> dict[str, Any] | None:
        return self.world["entidades"].get(entity_id)

    def update(self, entity_id: str, **changes: Any) -> dict[str, Any]:
        entity = self.get(entity_id)
        if not entity:
            raise KeyError("Entidade não encontrada")
        entity.update(changes)
        entity["atualizado_em"] = utc_now()
        return entity

    def act_npc(self, entity_id: str, available_actions: list[dict[str, Any]]) -> dict[str, Any]:
        """Seleciona uma ação sem inventar recursos: pontuação usa apenas estado declarado."""
        npc = self.get(entity_id)
        if not npc:
            raise KeyError("NPC não encontrado")
        if not available_actions:
            return {"acao": "nenhuma", "motivo": "nenhuma ação disponível"}
        goals = {g.lower() for g in npc.get("objetivos", [])}
        scored = []
        for action in available_actions:
            text = str(action.get("descricao", "")).lower()
            score = sum(1 for goal in goals if goal in text)
            score += float(action.get("seguranca", 0)) * 0.1
            scored.append((score, action))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[0][1]
