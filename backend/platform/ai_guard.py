from __future__ import annotations

"""Guard rails determinísticos para o ciclo de decisão da IA."""
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Decision:
    tool: str
    arguments: dict[str, Any]
    reason: str = ""


@dataclass
class DecisionResult:
    accepted: bool
    result: Any = None
    error: str | None = None


class ToolPolicy:
    def __init__(self):
        self.read_only = {"consultar_mundo", "buscar_memoria", "buscar_fontes", "consultar_npc"}
        self.mutating = {"avancar_tempo", "alterar_estado", "registrar_evento", "criar_entidade", "mover_entidade"}

    def check(self, decision: Decision) -> None:
        if not decision.tool:
            raise ValueError("Ferramenta ausente")
        if not isinstance(decision.arguments, dict):
            raise ValueError("Argumentos da ferramenta devem ser objeto")
        if decision.tool in self.mutating and not decision.reason.strip():
            raise ValueError("Ferramenta mutável exige justificativa causal")


class DecisionGuard:
    def __init__(self, tool_call: Callable[[str, dict[str, Any]], Any]):
        self.tool_call = tool_call
        self.policy = ToolPolicy()

    def execute(self, decision: Decision) -> DecisionResult:
        try:
            self.policy.check(decision)
            result = self.tool_call(decision.tool, decision.arguments)
            return DecisionResult(True, result=result)
        except (ValueError, KeyError, TypeError) as exc:
            return DecisionResult(False, error=str(exc))


class ContradictionDetector:
    """Detecta afirmações incompatíveis sem apagar histórico."""

    def compare(self, old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any] | None:
        if old.get("world_id") != new.get("world_id"):
            return None
        if old.get("entity_id") != new.get("entity_id"):
            return None
        field = new.get("field")
        if not field or field not in old or "value" not in new:
            return None
        if old[field] != new["value"]:
            return {"contradicao": True, "field": field, "anterior": old[field], "novo": new["value"]}
        return {"contradicao": False}
