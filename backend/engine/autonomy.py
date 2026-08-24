from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class Decision:
    entity_id: str
    action: str
    reason: str
    priority: float
    target: str | None = None

class AutonomyEngine:
    """Decisor determinístico de baixa complexidade; nunca altera estado sozinho."""
    def decide(self, entity: dict[str, Any]) -> Decision:
        needs = entity.get("needs", {})
        attrs = entity.get("attributes", {})
        if not entity.get("alive", True):
            return Decision(str(entity["id"]), "nenhuma", "entidade morta", 0)
        hunger = float(needs.get("fome", 0)); thirst = float(needs.get("sede", 0)); sleep = float(needs.get("sono", 0)); stress = float(needs.get("estresse", 0))
        if thirst >= 80: return Decision(str(entity["id"]), "buscar_agua", "sede crítica", thirst)
        if hunger >= 80: return Decision(str(entity["id"]), "buscar_alimento", "fome crítica", hunger)
        if sleep >= 85: return Decision(str(entity["id"]), "dormir", "privação de sono", sleep)
        if stress >= 85: return Decision(str(entity["id"]), "descansar", "estresse elevado", stress)
        activity = str(attrs.get("atividade", "repouso"))
        if activity in {"trabalho", "comercio", "estudo"}: return Decision(str(entity["id"]), activity, "rotina atual", 40)
        goals = entity.get("goals") or []
        if goals:
            goal = goals[0] if isinstance(goals[0], dict) else {"nome": str(goals[0])}
            return Decision(str(entity["id"]), "prosseguir_objetivo", "objetivo ativo", float(goal.get("prioridade", 30)), goal.get("alvo"))
        return Decision(str(entity["id"]), "repousar", "sem necessidade urgente", 10)

    def plan(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [asdict(self.decide(e)) for e in entities]
