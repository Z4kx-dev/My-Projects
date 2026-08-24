from __future__ import annotations

from dataclasses import dataclass

from .ingest import TextChunk


@dataclass(frozen=True)
class Citation:
    citation_id: str
    source_id: str
    source_name: str
    chunk_id: str
    ordinal: int
    excerpt: str
    score: float
    metadata: dict[str, str]

    @property
    def marker(self) -> str:
        return f"[{self.citation_id}]"


def citations(results: list[tuple[TextChunk, float]], source_names: dict[str, str] | None = None) -> list[Citation]:
    names = source_names or {}
    return [
        Citation(
            citation_id=f"S{index}",
            source_id=chunk.source_id,
            source_name=names.get(chunk.source_id, chunk.source_id),
            chunk_id=chunk.chunk_id,
            ordinal=chunk.ordinal,
            excerpt=chunk.text[:500],
            score=round(score, 6),
            metadata=dict(chunk.metadata),
        )
        for index, (chunk, score) in enumerate(results, 1)
    ]
