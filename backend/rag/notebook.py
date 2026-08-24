from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .citations import Citation, citations
from .ingest import DocumentIngestor, SourceDocument
from .vector_store import VectorStore


@dataclass
class NotebookWorkspace:
    """Coleção documental isolada por mundo/campanha."""

    notebook_id: str
    root: Path
    documents: dict[str, SourceDocument] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.sources_path = self.root / "sources.json"
        self.index = VectorStore(self.root / "index.json")
        self.ingestor = DocumentIngestor()
        self._load_sources()

    def _load_sources(self) -> None:
        if not self.sources_path.exists():
            return
        import json
        data = json.loads(self.sources_path.read_text(encoding="utf-8"))
        self.documents = {k: SourceDocument(**v) for k, v in data.items()}

    def _save_sources(self) -> None:
        import json
        tmp = self.sources_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({k: vars(v) for k, v in self.documents.items()}, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.sources_path)

    def add_text(self, name: str, text: str, mime_type: str = "text/plain", metadata: dict[str, str] | None = None) -> SourceDocument:
        document = self.ingestor.from_text(name, text, mime_type, metadata)
        chunks = self.ingestor.chunk(document)
        self.documents[document.source_id] = document
        self.index.upsert(chunks)
        self._save_sources()
        return document

    def add_file(self, path: str | Path, metadata: dict[str, str] | None = None) -> SourceDocument:
        document = self.ingestor.from_file(path, metadata)
        self.index.upsert(self.ingestor.chunk(document))
        self.documents[document.source_id] = document
        self._save_sources()
        return document

    def search(self, query: str, limit: int = 8, source_id: str | None = None) -> list[Citation]:
        results = self.index.search(query, limit, source_id)
        names = {sid: doc.name for sid, doc in self.documents.items()}
        return citations(results, names)

    def context(self, query: str, limit: int = 6, max_chars: int = 7000) -> tuple[str, list[Citation]]:
        refs = self.search(query, limit)
        blocks: list[str] = []
        used = 0
        for ref in refs:
            block = f"{ref.marker} {ref.source_name} (trecho {ref.ordinal + 1})\n{ref.excerpt}"
            if used + len(block) > max_chars:
                break
            blocks.append(block)
            used += len(block)
        return "\n\n".join(blocks), refs[: len(blocks)]
