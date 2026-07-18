"""
Person 1's full ingestion pipeline: load -> clean -> persist RawDocuments ->
chunk -> persist DocumentChunks.

No specific pipeline class/function name is mandated by the interfaces in
`interfaces/` (`data_provider_interface.py`'s `DocumentProvider`/
`ChunkProvider`/`DatasetLoader` are the *reading* contract consumed by
`providers/real_providers.py`, not a writing contract) — this module is the
producer that fills `data/processed/` and `data/chunks/` for those providers
to read, per the file layout documented in `README.md`.

Run directly with `python -m src.preprocessing.pipeline` to (re)generate
`data/processed/*.json` and `data/chunks/chunks.jsonl` from `data/raw/` (no
web sources configured by default — pass `web_urls` to `run_pipeline` to add
some).
"""
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import List, Optional

from src.core.logging_config import get_logger
from src.preprocessing.chunking.token_chunker import TokenChunker
from src.preprocessing.cleaning.french_medical_cleaner import FrenchMedicalCleaner
from src.preprocessing.interfaces.document_loader_interface import (
    DocumentChunk,
    DocumentLoader,
    RawDocument,
    TextChunker,
    TextCleaner,
)
from src.preprocessing.loaders.pdf_loader import MinsanteDocPDFLoader
from src.preprocessing.loaders.web_loader import OMSMarocWebLoader

logger = get_logger(__name__)

_CHUNKS_FILENAME = "chunks.jsonl"


@dataclass
class PipelineSummary:
    documents_processed: int
    documents_skipped: int
    chunks_generated: int


def run_pipeline(
    loaders: Optional[List[DocumentLoader]] = None,
    cleaner: Optional[TextCleaner] = None,
    chunker: Optional[TextChunker] = None,
    pdf_source_dir: "str | Path" = "data/raw",
    web_urls: Optional[List[str]] = None,
    processed_dir: "str | Path" = "data/processed",
    chunks_dir: "str | Path" = "data/chunks",
) -> PipelineSummary:
    """Runs the full pipeline and returns a summary of what happened.

    `loaders`/`cleaner`/`chunker` default to the real
    `MinsanteDocPDFLoader`/`OMSMarocWebLoader`, `FrenchMedicalCleaner`, and
    `TokenChunker`. Pass your own (e.g. a fake `DocumentLoader` returning
    canned `RawDocument`s) to exercise this against synthetic data without
    touching PDFs, the network, or the real `data/` directories.

    A document that fails to clean or chunk is skipped (logged as a
    warning) without stopping the rest of the batch.
    """
    if loaders is None:
        loaders = [MinsanteDocPDFLoader(source_dir=pdf_source_dir), OMSMarocWebLoader(urls=web_urls or [])]
    if cleaner is None:
        cleaner = FrenchMedicalCleaner()
    if chunker is None:
        chunker = TokenChunker()

    processed_dir = Path(processed_dir)
    chunks_dir = Path(chunks_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    documents: List[RawDocument] = []
    for loader in loaders:
        documents.extend(loader.load())

    all_chunks: List[DocumentChunk] = []
    documents_processed = 0
    documents_skipped = 0

    for document in documents:
        try:
            cleaned_document = replace(document, content=cleaner.clean(document.content))
            _write_document_json(cleaned_document, processed_dir)
            all_chunks.extend(chunker.chunk(cleaned_document))
        except Exception as exc:
            logger.warning("Skipping document %s: %s", document.source_id, exc)
            documents_skipped += 1
            continue
        documents_processed += 1

    _write_chunks_jsonl(all_chunks, chunks_dir / _CHUNKS_FILENAME)

    summary = PipelineSummary(
        documents_processed=documents_processed,
        documents_skipped=documents_skipped,
        chunks_generated=len(all_chunks),
    )
    logger.info(
        "Pipeline complete: %d document(s) processed, %d skipped, %d chunk(s) generated",
        summary.documents_processed,
        summary.documents_skipped,
        summary.chunks_generated,
    )
    return summary


def _write_document_json(document: RawDocument, processed_dir: Path) -> None:
    path = processed_dir / f"{document.source_id}.json"
    path.write_text(json.dumps(asdict(document), ensure_ascii=False, indent=2), encoding="utf-8")


def _write_chunks_jsonl(chunks: List[DocumentChunk], path: Path) -> None:
    lines = [json.dumps(asdict(chunk), ensure_ascii=False) for chunk in chunks]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


if __name__ == "__main__":
    run_pipeline()
