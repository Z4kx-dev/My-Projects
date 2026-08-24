from __future__ import annotations

import hashlib
from typing import Any
from backend.core.models import Event, utc_now
from .time import WorldClock


class SimulationEngine:
    def __init__(self, world: dict[str, Any]):
        self.world = world
        self.world.setdefault("tempo", {})
        self.world.setdefault("eventos", [])
        self.world.setdefault("entidades", {})

    def advance(self, seconds: int, reason: str = "passagem do tempo") -> dict[str, Any]:
        clock = WorldClock(self.world["tempo"].get("atual"))
        current = clock.advance(seconds)
        self.world["tempo"]["atual"] = current
        self.world["tempo"]["ultimo_avanco"] = {"segundos": seconds, "motivo": reason, "em": utc_now()}
        self.world["versao"] = int(self.world.get("versao", 1)) + 1
        return self.world

    def event(self, tipo: str, descricao: str, entidades: list[str] | None = None, consequencias: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        stamp = self.world["tempo"].get("atual") or utc_now()
        raw = f"{self.world['id']}|{stamp}|{tipo}|{descricao}"
        event = Event(hashlib.sha256(raw.encode()).hexdigest()[:16], self.world["id"], tipo, descricao, stamp, entidades=entidades or [], consequencias=consequencias or [])
        self.world["eventos"].append(event.__dict__)
        self.world["versao"] = int(self.world.get("versao", 1)) + 1
        return event.__dict__
