from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
import math

UTC = timezone.utc


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Memory:
    id: str
    world_id: str
    kind: str
    content: str
    importance: float = 0.5
    confidence: float = 1.0
    created_at: str = ""
    updated_at: str = ""
    source: str = "system"
    entity_ids: list[str] | None = None
    tags: list[str] | None = None
    supersedes: str | None = None
    expires_at: str | None = None

    def __post_init__(self):
        self.created_at = self.created_at or _now()
        self.updated_at = self.updated_at or self.created_at
        self.entity_ids = self.entity_ids or []
        self.tags = self.tags or []


class MemoryLayers:
    KINDS = {"episodica", "semantica", "procedural", "social", "estado", "mundial"}

    def __init__(self):
        self.items: dict[str, Memory] = {}

    def add(self, memory: Memory) -> Memory:
        if memory.kind not in self.KINDS:
            raise ValueError(f"Tipo de memória inválido: {memory.kind}")
        if not 0 <= memory.importance <= 1 or not 0 <= memory.confidence <= 1:
            raise ValueError("importance/confidence devem estar entre 0 e 1")
        self.items[memory.id] = memory
        return memory

    def rank(self, query: str, world_id: str, limit: int = 12) -> list[dict[str, Any]]:
        terms = set(query.lower().split())
        ranked = []
        for memory in self.items.values():
            if memory.world_id != world_id:
                continue
            text_terms = set(memory.content.lower().split())
            overlap = len(terms & text_terms) / max(1, len(terms))
            score = overlap * 0.6 + memory.importance * 0.25 + memory.confidence * 0.15
            if score > 0:
                ranked.append((score, memory))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [{"score": round(score, 5), **asdict(memory)} for score, memory in ranked[:limit]]

    def consolidate(self, world_id: str) -> list[Memory]:
        """Mantém memórias recentes e importantes; preserva histórico e aponta substituições."""
        grouped: dict[str, list[Memory]] = {}
        for memory in self.items.values():
            if memory.world_id == world_id:
                key = " ".join(sorted(memory.tags)) or memory.content[:80].lower()
                grouped.setdefault(key, []).append(memory)
        merged: list[Memory] = []
        for group in grouped.values():
            if len(group) < 2:
                continue
            winner = max(group, key=lambda x: (x.importance, x.confidence, x.updated_at))
            for item in group:
                if item.id != winner.id:
                    item.supersedes = winner.id
                    item.updated_at = _now()
            merged.append(winner)
        return merged
