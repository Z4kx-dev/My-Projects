from __future__ import annotations

import hashlib
from typing import Any
from backend.core.models import Memory, utc_now
from backend.core.storage import JsonStore


class MemoryStore:
    def __init__(self, store: JsonStore):
        self.store = store

    def _id(self, world_id: str, content: str) -> str:
        return hashlib.sha256(f"{world_id}:{content}".encode("utf-8")).hexdigest()[:16]

    def add(self, world_id: str, content: str, tipo: str = "fato", importancia: float = 0.5, tags: list[str] | None = None, origem: str = "simulacao") -> dict[str, Any]:
        content = content.strip()
        if not content:
            raise ValueError("Memória vazia")
        importance = max(0.0, min(1.0, float(importancia)))
        memory = Memory(self._id(world_id, content), world_id, tipo, content, importance, tags or [], origem)
        existing = self.get(world_id, memory.id)
        if existing:
            existing["importancia"] = max(existing.get("importancia", 0.0), importance)
            existing["tags"] = sorted(set(existing.get("tags", [])) | set(tags or []))
            existing["atualizado_em"] = utc_now()
            self.store.write(existing, "mundos", world_id, "memoria", f"{memory.id}.json")
            return existing
        data = memory.__dict__
        self.store.write(data, "mundos", world_id, "memoria", f"{memory.id}.json")
        return data

    def get(self, world_id: str, memory_id: str) -> dict[str, Any] | None:
        return self.store.read("mundos", world_id, "memoria", f"{memory_id}.json")

    def update(self, world_id: str, memory_id: str, **changes: Any) -> dict[str, Any] | None:
        item = self.get(world_id, memory_id)
        if not item:
            return None
        if "conteudo" in changes:
            content = str(changes["conteudo"]).strip()
            if not content:
                raise ValueError("Memória vazia")
        else:
            content = item.get("conteudo", "")
        item["conteudo"] = content
        if "tipo" in changes:
            item["tipo"] = str(changes["tipo"])
        if "importancia" in changes:
            item["importancia"] = max(0.0, min(1.0, float(changes["importancia"])))
        if "tags" in changes:
            if not isinstance(changes["tags"], list):
                raise ValueError("tags deve ser uma lista")
            item["tags"] = [str(x) for x in changes["tags"]]
        item["atualizado_em"] = utc_now()
        self.store.write(item, "mundos", world_id, "memoria", f"{memory_id}.json")
        return item

    def delete(self, world_id: str, memory_id: str) -> bool:
        return self.store.delete("mundos", world_id, "memoria", f"{memory_id}.json")

    def list(self, world_id: str) -> list[dict[str, Any]]:
        root = self.store.path("mundos", world_id, "memoria")
        if not root.exists():
            return []
        result = []
        for p in root.glob("*.json"):
            item = self.store.read("mundos", world_id, "memoria", p.name)
            if item and item.get("valido", True):
                result.append(item)
        return sorted(result, key=lambda x: (x.get("importancia", 0), x.get("atualizado_em", "")), reverse=True)

    def search(self, world_id: str, query: str, limit: int = 12) -> list[dict[str, Any]]:
        terms = {t.lower() for t in query.split() if len(t) > 2}
        scored = []
        for item in self.list(world_id):
            text = (item.get("conteudo", "") + " " + " ".join(item.get("tags", []))).lower()
            score = sum(1 for term in terms if term in text) / max(1, len(terms))
            if score:
                score += float(item.get("importancia", 0)) * 0.25
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:max(1, limit)]]
