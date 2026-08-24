from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Person:
    id: str
    name: str
    age_years: float = 18.0
    alive: bool = True
    household_id: str | None = None
    occupation: str | None = None
    wealth: float = 0.0
    traits: dict[str, float] = field(default_factory=dict)

    def age(self, years: float) -> None:
        if years < 0:
            raise ValueError("tempo negativo")
        self.age_years += years


@dataclass
class Household:
    id: str
    members: list[str] = field(default_factory=list)
    wealth: float = 0.0


@dataclass
class Population:
    people: dict[str, Person] = field(default_factory=dict)
    households: dict[str, Household] = field(default_factory=dict)

    def living_count(self) -> int:
        return sum(1 for p in self.people.values() if p.alive)
