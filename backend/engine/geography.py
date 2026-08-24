from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Location:
    id: str
    name: str
    latitude: float | None = None
    longitude: float | None = None
    terrain: str = "desconhecido"
    elevation_m: float = 0.0
    neighbors: list[str] = field(default_factory=list)


@dataclass
class Route:
    origin: str
    destination: str
    distance_km: float
    terrain_multiplier: float = 1.0

    def travel_hours(self, speed_kmh: float) -> float:
        if speed_kmh <= 0:
            raise ValueError("velocidade deve ser positiva")
        return self.distance_km * self.terrain_multiplier / speed_kmh
