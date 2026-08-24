from __future__ import annotations

from pathlib import Path


class UnsupportedDocumentError(ValueError):
    pass


def extract_text(path: str | Path) -> tuple[str, str]:
    """Extrai texto de PDF/DOCX com bibliotecas explícitas.

    Retorna (texto, mime_type). Falhas de leitura não são convertidas em texto
    vazio, porque isso esconderia corrupção ou documentos sem conteúdo.
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(p))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        text = "\n\n".join(f"[Página {i + 1}]\n{value}" for i, value in enumerate(pages) if value)
        if not text.strip():
            raise ValueError("PDF não contém texto extraível.")
        return text, "application/pdf"
    if suffix == ".docx":
        from docx import Document
        doc = Document(str(p))
        paragraphs = [x.text.strip() for x in doc.paragraphs if x.text.strip()]
        text = "\n\n".join(paragraphs)
        if not text:
            raise ValueError("DOCX não contém texto extraível.")
        return text, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    raise UnsupportedDocumentError(f"Formato de extração não suportado: {suffix or '<sem extensão>'}")
