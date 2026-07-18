"""
DocumentLoader for local PDF files (e.g. Ministère de la Santé du Maroc guides).

Extracts raw text per page with pypdf and concatenates it into one
RawDocument per PDF file. Extraction only — no cleaning (TextCleaner) or
chunking (TextChunker), per the DocumentLoader contract.
"""
from pathlib import Path
from typing import Any, List

from pypdf import PdfReader

from src.core.logging_config import get_logger
from src.preprocessing.interfaces.document_loader_interface import DocumentLoader, RawDocument

logger = get_logger(__name__)


class MinsanteDocPDFLoader(DocumentLoader):
    """Loads every PDF file in a directory into one `RawDocument` each.

    Args:
        source_dir: Directory containing the PDFs to load.
        institution: Stored in metadata["institution"] for all documents
            loaded by this instance (e.g. "Ministère de la Santé").
        language: Stored in metadata["language"].
    """

    def __init__(
        self,
        source_dir: str | Path = "data/raw",
        institution: str = "Ministère de la Santé",
        language: str = "fr",
    ) -> None:
        self.source_dir = Path(source_dir)
        self.institution = institution
        self.language = language

    def load(self) -> List[RawDocument]:
        documents: List[RawDocument] = []
        for pdf_path in sorted(self.source_dir.glob("*.pdf")):
            try:
                documents.append(self._load_one(pdf_path))
            except Exception as exc:
                logger.warning("Skipping unreadable PDF %s: %s", pdf_path.name, exc)
        return documents

    def _load_one(self, pdf_path: Path) -> RawDocument:
        reader = PdfReader(str(pdf_path))
        if reader.is_encrypted:
            raise ValueError("encrypted PDF")
        content = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()

        pdf_meta = reader.metadata or {}
        title = pdf_meta.get("/Title") or pdf_path.stem

        metadata: dict[str, Any] = {
            "institution": self.institution,
            "language": self.language,
            "num_pages": len(reader.pages),
        }

        return RawDocument(
            source_id=pdf_path.stem,
            title=title,
            content=content,
            source_url=str(pdf_path),
            metadata=metadata,
        )
