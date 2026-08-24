"""RAG local, persistente e independente do provedor de LLM."""

from .ingest import DocumentIngestor, SourceDocument, TextChunk
from .vector_store import VectorStore
from .notebook import NotebookWorkspace

__all__ = ["DocumentIngestor", "SourceDocument", "TextChunk", "VectorStore", "NotebookWorkspace"]
