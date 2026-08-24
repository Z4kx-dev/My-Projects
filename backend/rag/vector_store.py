from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
import re
from typing import Iterable

from .ingest import TextChunk


class VectorStore:
    """Índice vetorial local sem dependência obrigatória de serviço externo.

    Usa hashing de tokens como representação esparsa. A interface é compatível
    com um backend de embeddings real no futuro, sem acoplar o restante da app.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.chunks: dict[str, TextChunk] = {}
        self.vectors: dict[str, dict[str, float]] = {}
        self.doc_freq: dict[str, int] = {}
        if self.path and self.path.exists():
            self.load()

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[\wÀ-ÿ]{2,}", text.lower())

    def _vector(self, text: str) -> dict[str, float]:
        tokens = self._tokens(text)
        if not tokens:
            return {}
        counts: dict[str, float] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0.0) + 1.0
        total = float(len(tokens))
        return {k: v / total for k, v in counts.items()}

    def upsert(self, chunks: Iterable[TextChunk]) -> int:
        count = 0
        for chunk in chunks:
            old = self.chunks.get(chunk.chunk_id)
            if old is not None:
                self._remove_freq(self.vectors.get(chunk.chunk_id, {}))
            self.chunks[chunk.chunk_id] = chunk
            vector = self._vector(chunk.text)
            self.vectors[chunk.chunk_id] = vector
            for token in vector:
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1
            count += 1
        if self.path:
            self.save()
        return count

    def _remove_freq(self, vector: dict[str, float]) -> None:
        for token in vector:
            value = self.doc_freq.get(token, 0) - 1
            if value <= 0:
                self.doc_freq.pop(token, None)
            else:
                self.doc_freq[token] = value

    def search(self, query: str, limit: int = 8, source_id: str | None = None) -> list[tuple[TextChunk, float]]:
        if limit <= 0:
            return []
        q = self._vector(query)
        if not q:
            return []
        n = max(1, len(self.chunks))
        qweights = {k: v * math.log((n + 1) / (self.doc_freq.get(k, 0) + 1)) for k, v in q.items()}
        qnorm = math.sqrt(sum(v * v for v in qweights.values())) or 1.0
        scored: list[tuple[TextChunk, float]] = []
        for cid, vector in self.vectors.items():
            chunk = self.chunks[cid]
            if source_id and chunk.source_id != source_id:
                continue
            weights = {k: v * math.log((n + 1) / (self.doc_freq.get(k, 0) + 1)) for k, v in vector.items()}
            norm = math.sqrt(sum(v * v for v in weights.values())) or 1.0
            dot = sum(qweights.get(k, 0.0) * v for k, v in weights.items())
            score = dot / (qnorm * norm)
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "chunks": [asdict(c) for c in self.chunks.values()],
            "vectors": self.vectors,
            "doc_freq": self.doc_freq,
        }
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("version") != 1:
            raise ValueError("Versão de índice RAG incompatível")
        self.chunks = {c["chunk_id"]: TextChunk(**c) for c in payload.get("chunks", [])}
        self.vectors = {k: {str(t): float(v) for t, v in vec.items()} for k, vec in payload.get("vectors", {}).items()}
        self.doc_freq = {str(k): int(v) for k, v in payload.get("doc_freq", {}).items()}
