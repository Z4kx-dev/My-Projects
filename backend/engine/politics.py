from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Law:
    id: str
    title: str
    description: str
    active: bool = True


@dataclass
class Government:
    name: str
    laws: dict[str, Law] = field(default_factory=dict)
    treasury: float = 0.0
    legitimacy: float = 50.0
    relations: dict[str, float] = field(default_factory=dict)

    def enact(self, law: Law) -> None:
        self.laws[law.id] = law
