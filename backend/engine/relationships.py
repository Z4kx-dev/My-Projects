from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Relationship:
    source: str
    target: str
    affinity: float = 0.0
    trust: float = 0.0
    fear: float = 0.0
    respect: float = 0.0
    history: list[str] = field(default_factory=list)

    def clamp(self) -> None:
        for field_name in ("affinity", "trust", "fear", "respect"):
            setattr(self, field_name, max(-100.0, min(100.0, getattr(self, field_name))))
