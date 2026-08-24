from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanStep:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


class ToolPlanner:
    """Planeja chamadas de ferramentas sem executar efeitos colaterais sozinho."""

    def build(self, requested_tools: list[dict[str, Any]]) -> list[PlanStep]:
        return [
            PlanStep(
                tool=item["name"],
                arguments=item.get("arguments", {}),
                reason=item.get("reason", "")
            )
            for item in requested_tools
            if isinstance(item, dict) and item.get("name")
        ]
