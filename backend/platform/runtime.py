from __future__ import annotations

"""Runtime integrado para campanhas persistentes.

A camada não substitui o LLM: mantém o estado do mundo como fonte de verdade,
registra eventos, memória, snapshots e valida mutações antes de aplicá-las.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from copy import deepcopy
from hashlib import sha256
import json
import math
import os
import random
from typing import Any


UTC = timezone.utc


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


@dataclass
class Event:
    id: str
    world_id: str
    kind: str
    at: str
    payload: dict[str, Any]
    causes: list[str] = field(default_factory=list)
    source: str = "system"


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    world_id: str
    attributes: dict[str, Any] = field(default_factory=dict)
    needs: dict[str, float] = field(default_factory=dict)
    goals: list[dict[str, Any]] = field(default_factory=list)
    relations: dict[str, float] = field(default_factory=dict)
    memory_ids: list[str] = field(default_factory=list)
    alive: bool = True


class ValidationError(ValueError):
    pass


class StateValidator:
    """Invariantes centrais; falhas são rejeitadas antes de persistir."""

    REQUIRED_WORLD_KEYS = ("id", "nome", "tipo")

    def validate_world(self, world: dict[str, Any]) -> None:
        for key in self.REQUIRED_WORLD_KEYS:
            if not world.get(key):
                raise ValidationError(f"Campo obrigatório ausente: {key}")
        if not isinstance(world.get("id"), str):
            raise ValidationError("world.id deve ser string")
        if not isinstance(world.get("regras", {}), dict):
            raise ValidationError("world.regras deve ser objeto")

    def validate_entity(self, entity: dict[str, Any]) -> None:
        if not entity.get("id") or not entity.get("world_id"):
            raise ValidationError("Entidade sem id/world_id")
        attrs = entity.get("attributes", {})
        for key, value in attrs.items():
            if key.endswith("_pct") and not 0 <= float(value) <= 100:
                raise ValidationError(f"Atributo percentual inválido: {key}")
        if entity.get("alive") is False and entity.get("needs", {}).get("vitalidade", 1) > 0:
            # Morte pode existir por causas externas, mas não deve coexistir com
            # vitalidade positiva sem um motivo explicitamente registrado.
            if not entity.get("attributes", {}).get("death_cause"):
                raise ValidationError("Morte sem causa registrada")


class CausalLedger:
    def __init__(self) -> None:
        self.events: dict[str, Event] = {}

    def append(self, event: Event) -> Event:
        if event.id in self.events:
            raise ValidationError(f"Evento duplicado: {event.id}")
        self.events[event.id] = event
        return event

    def explain(self, event_id: str) -> list[Event]:
        seen: set[str] = set()
        out: list[Event] = []
        def walk(eid: str) -> None:
            if eid in seen or eid not in self.events:
                return
            seen.add(eid)
            event = self.events[eid]
            for parent in event.causes:
                walk(parent)
            out.append(event)
        walk(event_id)
        return out


class EventScheduler:
    def __init__(self) -> None:
        self.queue: list[Event] = []

    def schedule(self, event: Event) -> None:
        self.queue.append(event)
        self.queue.sort(key=lambda x: x.at)

    def due(self, at: str) -> list[Event]:
        ready = [e for e in self.queue if e.at <= at]
        self.queue = [e for e in self.queue if e.at > at]
        return ready


class NeedsEngine:
    """Modelo simples e extensível de necessidades; não inventa dano."""

    DEFAULTS = {"fome": 0.0, "sede": 0.0, "sono": 0.0, "estresse": 0.0}

    def tick(self, entity: Entity, hours: float, activity: str = "repouso") -> dict[str, float]:
        if not entity.alive:
            return entity.needs
        rate = {"repouso": 1.0, "trabalho": 1.35, "combate": 2.5, "viagem": 1.8}.get(activity, 1.2)
        for key, base in self.DEFAULTS.items():
            entity.needs[key] = clamp(entity.needs.get(key, base) + hours * 2.0 * rate)
        if activity == "repouso":
            entity.needs["sono"] = clamp(entity.needs["sono"] - hours * 5.0)
        return entity.needs


class EconomyEngine:
    def price(self, base: float, stock: float, demand: float, scarcity: float = 1.0) -> float:
        if base < 0:
            raise ValidationError("Preço base negativo")
        ratio = demand / max(stock, 0.01)
        multiplier = 1.0 + 0.35 * math.tanh((ratio - 1.0) * scarcity)
        return round(max(0.01, base * multiplier), 2)

    def transaction(self, buyer: dict[str, Any], seller: dict[str, Any], price: float, quantity: int = 1) -> None:
        total = round(price * quantity, 2)
        if quantity <= 0 or total < 0:
            raise ValidationError("Transação inválida")
        if float(buyer.get("money", 0)) < total:
            raise ValidationError("Saldo insuficiente")
        if int(seller.get("stock", 0)) < quantity:
            raise ValidationError("Estoque insuficiente")
        buyer["money"] = round(float(buyer.get("money", 0)) - total, 2)
        seller["money"] = round(float(seller.get("money", 0)) + total, 2)
        seller["stock"] = int(seller.get("stock", 0)) - quantity


class CombatEngine:
    """Resolve um ataque por fatores observáveis; sem HP oculto."""

    def attack(self, attacker: Entity, defender: Entity, weapon: dict[str, Any], rng: random.Random | None = None) -> dict[str, Any]:
        rng = rng or random.Random()
        if not attacker.alive or not defender.alive:
            raise ValidationError("Combatentes incapacitados não podem atacar")
        strength = clamp(attacker.attributes.get("forca", 50))
        skill = clamp(attacker.attributes.get("tecnica", 20))
        defense = clamp(defender.attributes.get("defesa", 50))
        fatigue = clamp(attacker.attributes.get("fadiga_pct", 0))
        reach = max(0.1, float(weapon.get("alcance", 1.0)))
        power = max(0.1, float(weapon.get("potencia", 10)))
        score = strength * 0.35 + skill * 0.45 + reach * 5 + rng.uniform(-10, 10) - fatigue * 0.2
        hit = score >= defense * 0.8
        severity = max(0.0, (score - defense * 0.6) / 100.0) * power if hit else 0.0
        return {"acertou": hit, "severidade": round(severity, 3), "defesa": round(defense, 2), "score": round(score, 2)}


class PopulationEngine:
    def birth(self, population: dict[str, Any], count: int = 1) -> None:
        population["nascimentos"] = int(population.get("nascimentos", 0)) + max(0, count)
        population["total"] = int(population.get("total", 0)) + max(0, count)

    def death(self, population: dict[str, Any], count: int = 1) -> None:
        count = max(0, count)
        population["mortes"] = int(population.get("mortes", 0)) + count
        population["total"] = max(0, int(population.get("total", 0)) - count)


class SnapshotManager:
    def __init__(self, root: str) -> None:
        self.root = root

    def save(self, world_id: str, state: dict[str, Any], label: str = "manual") -> dict[str, Any]:
        payload = {"schema": 1, "world_id": world_id, "label": label, "created_at": now_iso(), "state": deepcopy(state)}
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        digest = sha256(raw).hexdigest()
        payload["sha256"] = digest
        directory = os.path.join(self.root, "worlds", world_id, "snapshots")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"{digest[:16]}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return {"id": digest[:16], "sha256": digest, "path": path, "created_at": payload["created_at"]}


class RPGRuntime:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.validator = StateValidator()
        self.causal = CausalLedger()
        self.scheduler = EventScheduler()
        self.needs = NeedsEngine()
        self.economy = EconomyEngine()
        self.combat = CombatEngine()
        self.population = PopulationEngine()
        self.snapshots = SnapshotManager(data_dir)
        self.entities: dict[str, Entity] = {}

    def register_entity(self, entity: Entity) -> Entity:
        self.validator.validate_entity(asdict(entity))
        if entity.id in self.entities:
            raise ValidationError(f"Entidade já existe: {entity.id}")
        self.entities[entity.id] = entity
        return entity

    def advance(self, world: dict[str, Any], hours: float) -> dict[str, Any]:
        self.validator.validate_world(world)
        if hours <= 0:
            raise ValidationError("O avanço temporal deve ser positivo")
        current = world.setdefault("tempo", {}).get("iso") or now_iso()
        current_dt = datetime.fromisoformat(current.replace("Z", "+00:00"))
        target = current_dt + timedelta(hours=hours)
        world.setdefault("tempo", {})["iso"] = target.isoformat()
        world["tempo"]["horas_decorridas"] = float(world["tempo"].get("horas_decorridas", 0)) + hours
        due = self.scheduler.due(target.isoformat())
        return {"tempo": world["tempo"], "eventos": [asdict(x) for x in due]}
