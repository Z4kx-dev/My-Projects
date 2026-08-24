from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import math


def clamp(x: float, a: float = 0, b: float = 100) -> float:
    return max(a, min(b, float(x)))


@dataclass
class Weather:
    temperature_c: float = 20.0
    precipitation_mm: float = 0.0
    wind_kmh: float = 0.0
    humidity_pct: float = 50.0
    season: str = "desconhecida"


@dataclass
class Location:
    id: str
    name: str
    kind: str
    x: float = 0.0
    y: float = 0.0
    population: int = 0
    resources: dict[str, float] = field(default_factory=dict)
    infrastructure: dict[str, float] = field(default_factory=dict)


@dataclass
class Faction:
    id: str
    name: str
    government: str = "local"
    treasury: float = 0.0
    population: int = 0
    relations: dict[str, float] = field(default_factory=dict)
    laws: list[str] = field(default_factory=list)


class ClimateEngine:
    def tick(self, weather: Weather, latitude: float, day_of_year: int, altitude_m: float = 0) -> Weather:
        seasonal = 12.0 * math.sin((day_of_year - 80) * 2 * math.pi / 365)
        latitude_effect = abs(latitude) * 0.08
        altitude_effect = altitude_m * 0.0065
        weather.temperature_c = round(20 + seasonal - latitude_effect - altitude_effect, 2)
        weather.humidity_pct = clamp(weather.humidity_pct + (weather.precipitation_mm - 2) * 0.4)
        weather.wind_kmh = max(0, weather.wind_kmh)
        return weather


class GeographyEngine:
    def distance(self, a: Location, b: Location) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    def travel_hours(self, a: Location, b: Location, speed_kmh: float = 5.0, terrain_factor: float = 1.0) -> float:
        if speed_kmh <= 0 or terrain_factor <= 0:
            raise ValueError("Velocidade e fator de terreno devem ser positivos")
        return self.distance(a, b) / speed_kmh * terrain_factor


class SocietyEngine:
    def update_population(self, population: int, births: int, deaths: int, migration_in: int = 0, migration_out: int = 0) -> int:
        return max(0, population + births - deaths + migration_in - migration_out)

    def social_pressure(self, unemployment: float, food_shortage: float, inequality: float) -> float:
        return clamp(unemployment * 0.35 + food_shortage * 0.45 + inequality * 0.20)


class DiplomacyEngine:
    def relation_change(self, current: float, trade: float = 0, treaty: float = 0, conflict: float = 0, betrayal: float = 0) -> float:
        return clamp(current + trade * 0.10 + treaty * 0.25 - conflict * 0.40 - betrayal * 0.60, -100, 100)

    def war_pressure(self, attacker: Faction, defender: Faction, border_tension: float, casus_belli: float) -> float:
        relative = attacker.treasury / max(1.0, defender.treasury)
        return clamp(border_tension * 0.55 + casus_belli * 0.30 + min(100, relative * 15) * 0.15)


class MissionEngine:
    def create(self, mission_id: str, title: str, objective: str) -> dict[str, Any]:
        return {"id": mission_id, "title": title, "objective": objective, "status": "ativa", "progress": 0, "steps": []}

    def advance(self, mission: dict[str, Any], amount: float, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
        mission["progress"] = clamp(float(mission.get("progress", 0)) + amount)
        if evidence:
            mission.setdefault("evidence", []).append(evidence)
        if mission["progress"] >= 100:
            mission["progress"] = 100
            mission["status"] = "concluida"
        return mission
