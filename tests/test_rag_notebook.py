from pathlib import Path

from backend.rag.ingest import DocumentIngestor
from backend.rag.notebook import NotebookWorkspace
from backend.rag.vector_store import VectorStore


def test_chunking_preserva_documento():
    doc = DocumentIngestor().from_text("mundo.md", "A cidade de Aster possui um mercado.\n\nO rei governa a região.")
    chunks = DocumentIngestor().chunk(doc, max_chars=100, overlap=10)
    assert chunks
    assert all(c.source_id == doc.source_id for c in chunks)


def test_vector_store_retorna_termo_relevante(tmp_path: Path):
    ingestor = DocumentIngestor()
    doc = ingestor.from_text("fonte.txt", "Aster possui um grande mercado de trigo.")
    store = VectorStore(tmp_path / "index.json")
    store.upsert(ingestor.chunk(doc, max_chars=100))
    results = store.search("mercado trigo")
    assert results
    assert results[0][0].source_id == doc.source_id


def test_notebook_isola_fontes_e_produz_citacao(tmp_path: Path):
    notebook = NotebookWorkspace("mundo-1", tmp_path / "mundo-1")
    notebook.add_text("História", "Aster foi fundada no ano 120.")
    refs = notebook.search("fundada Aster")
    assert refs
    assert refs[0].source_name == "História"
    assert refs[0].marker == "[S1]"


def test_notebook_reabre_indice(tmp_path: Path):
    root = tmp_path / "mundo"
    first = NotebookWorkspace("m1", root)
    first.add_text("Lei", "A lei do reino exige registro comercial.")
    second = NotebookWorkspace("m1", root)
    assert second.search("registro comercial")
