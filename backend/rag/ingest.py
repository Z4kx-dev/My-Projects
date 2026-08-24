from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    name: str
    mime_type: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    source_id: str
    text: str
    ordinal: int
    start: int
    end: int
    metadata: dict[str, str] = field(default_factory=dict)


class DocumentIngestor:
    """Ingestão determinística para texto/Markdown/HTML/JSON simples.

    PDF/DOCX devem passar por adaptadores externos de extração; o núcleo não
    finge extrair formatos binários sem uma biblioteca apropriada.
    """

    TEXT_TYPES = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".html": "text/html",
        ".htm": "text/html",
        ".json": "application/json",
        ".csv": "text/csv",
    }

    def from_text(self, name: str, text: str, mime_type: str = "text/plain", metadata: dict[str, str] | None = None) -> SourceDocument:
        clean = self._normalize(text)
        source_id = hashlib.sha256(f"{name}\n{clean}".encode("utf-8")).hexdigest()[:24]
        return SourceDocument(source_id, name, mime_type, clean, metadata or {})

    def from_file(self, path: str | Path, metadata: dict[str, str] | None = None) -> SourceDocument:
        p = Path(path)
        mime = self.TEXT_TYPES.get(p.suffix.lower())
        if mime is None:
            raise ValueError(f"Formato não suportado pelo núcleo de ingestão: {p.suffix or '<sem extensão>'}")
        return self.from_text(p.name, p.read_text(encoding="utf-8"), mime, metadata)

    def chunk(self, document: SourceDocument, max_chars: int = 1200, overlap: int = 180) -> list[TextChunk]:
        if max_chars < 100:
            raise ValueError("max_chars deve ser >= 100")
        if overlap < 0 or overlap >= max_chars:
            raise ValueError("overlap deve estar entre 0 e max_chars-1")
        text = document.text
        chunks: list[TextChunk] = []
        start = 0
        ordinal = 0
        while start < len(text):
            limit = min(len(text), start + max_chars)
            cut = self._best_cut(text, start, limit)
            piece = text[start:cut].strip()
            if piece:
                cid = hashlib.sha256(f"{document.source_id}:{ordinal}:{piece}".encode()).hexdigest()[:24]
                chunks.append(TextChunk(cid, document.source_id, piece, ordinal, start, cut, dict(document.metadata)))
                ordinal += 1
            if cut >= len(text):
                break
            start = max(start + 1, cut - overlap)
        return chunks

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _best_cut(text: str, start: int, limit: int) -> int:
        if limit == len(text):
            return limit
        window = text[start:limit]
        for marker in ("\n\n", ". ", "! ", "? ", "\n", " "):
            pos = window.rfind(marker)
            if pos > len(window) * 0.55:
                return start + pos + len(marker)
        return limit

    def ingest(self, documents: Iterable[SourceDocument], max_chars: int = 1200, overlap: int = 180) -> list[TextChunk]:
        result: list[TextChunk] = []
        for document in documents:
            result.extend(self.chunk(document, max_chars, overlap))
        return result
