from __future__ import annotations

"""RAG local sem dependência externa obrigatória.

Implementa ingestão, chunking, índice lexical e ranking híbrido. Um backend de
embeddings pode ser plugado depois sem alterar o contrato público.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import math
from collections import Counter
from typing import Iterable


@dataclass
class Chunk:
    id: str
    source_id: str
    title: str
    text: str
    page: int | None = None
    metadata: dict = None

    def __post_init__(self):
        self.metadata = self.metadata or {}


class DocumentIngestor:
    EXTENSIONS = {".txt", ".md", ".markdown", ".html", ".htm", ".json", ".csv"}

    def read(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        if suffix not in self.EXTENSIONS:
            raise ValueError(f"Formato ainda não suportado pelo ingestão local: {suffix}")
        return Path(path).read_text(encoding="utf-8", errors="replace")

    def clean(self, text: str) -> str:
        text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
        text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def chunk(self, source_id: str, title: str, text: str, size: int = 1200, overlap: int = 180) -> list[Chunk]:
        text = self.clean(text)
        if size <= overlap or size < 100:
            raise ValueError("size deve ser maior que overlap e >= 100")
        out: list[Chunk] = []
        start = 0
        index = 0
        while start < len(text):
            end = min(len(text), start + size)
            piece = text[start:end]
            out.append(Chunk(f"{source_id}:{index}", source_id, title, piece, metadata={"start": start, "end": end}))
            index += 1
            if end >= len(text):
                break
            start = end - overlap
        return out


class LexicalIndex:
    STOP = {"a", "o", "e", "de", "do", "da", "em", "um", "uma", "que", "para", "por", "com", "os", "as"}

    def __init__(self):
        self.chunks: dict[str, Chunk] = {}
        self.tf: dict[str, Counter[str]] = {}
        self.df: Counter[str] = Counter()

    @staticmethod
    def tokens(text: str) -> list[str]:
        return [x for x in re.findall(r"[\wÀ-ÿ]+", text.lower()) if x not in LexicalIndex.STOP]

    def add(self, chunks: Iterable[Chunk]) -> None:
        for chunk in chunks:
            if chunk.id in self.chunks:
                continue
            self.chunks[chunk.id] = chunk
            terms = Counter(self.tokens(chunk.text))
            self.tf[chunk.id] = terms
            for term in terms:
                self.df[term] += 1

    def search(self, query: str, limit: int = 8) -> list[dict]:
        q = Counter(self.tokens(query))
        if not q:
            return []
        n = max(1, len(self.chunks))
        scores: list[tuple[float, Chunk]] = []
        for cid, terms in self.tf.items():
            score = 0.0
            for token, qtf in q.items():
                if token not in terms:
                    continue
                idf = math.log((n + 1) / (self.df[token] + 1)) + 1
                score += (1 + math.log(terms[token])) * idf * qtf
            if score:
                scores.append((score, self.chunks[cid]))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [{"score": round(score, 5), **asdict(chunk)} for score, chunk in scores[:limit]]


class RAGStore:
    def __init__(self):
        self.sources: dict[str, dict] = {}
        self.index = LexicalIndex()

    def add_source(self, source_id: str, title: str, text: str, metadata: dict | None = None) -> dict:
        source = {"id": source_id, "title": title, "metadata": metadata or {}, "chars": len(text)}
        self.sources[source_id] = source
        chunks = DocumentIngestor().chunk(source_id, title, text)
        self.index.add(chunks)
        source["chunks"] = len(chunks)
        return source

    def search(self, query: str, limit: int = 8) -> dict:
        results = self.index.search(query, limit)
        return {"query": query, "results": results, "sources": [self.sources.get(x["source_id"]) for x in results]}
