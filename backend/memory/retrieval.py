from __future__ import annotations

import math
from collections import Counter
from typing import Any
from .store import MemoryStore


class HybridRetriever:
    """Recuperação semântica opcional + lexical. Sem embeddings, funciona offline."""
    def __init__(self, memories: MemoryStore):
        self.memories = memories

    @staticmethod
    def _tfidf_score(query: str, text: str) -> float:
        q = [x.lower() for x in query.split() if len(x) > 2]
        words = [x.lower() for x in text.split() if len(x) > 2]
        if not q or not words:
            return 0.0
        counts = Counter(words)
        return sum(counts[t] for t in set(q)) / math.sqrt(len(words))

    def search(self, world_id: str, query: str, limit: int = 12) -> list[dict[str, Any]]:
        candidates = self.memories.list(world_id)
        scored = []
        for item in candidates:
            text = item.get("conteudo", "") + " " + " ".join(item.get("tags", []))
            lexical = self._tfidf_score(query, text)
            importance = float(item.get("importancia", 0))
            score = lexical + importance * 0.15
            if score > 0:
                copy = dict(item)
                copy["_score"] = round(score, 6)
                scored.append(copy)
        scored.sort(key=lambda x: x["_score"], reverse=True)
        return scored[: max(1, min(50, limit))]
