"""Page-aware production pipeline for official Ministry PDF documents.

Unlike the legacy loader, this pipeline never concatenates an entire PDF.
Each page is cleaned and chunked independently, retaining official URL,
filename, page number, document hash, and a best-effort section heading.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from pypdf import PdfReader

from src.core.logging_config import get_logger
from src.preprocessing.chunking.token_chunker import TokenChunker
from src.preprocessing.cleaning.french_medical_cleaner import FrenchMedicalCleaner
from src.preprocessing.interfaces.document_loader_interface import RawDocument

logger = get_logger(__name__)


@dataclass
class DocumentQuality:
    filename: str
    title: str
    pages_total: int = 0
    pages_with_text: int = 0
    pages_without_text: int = 0
    chunks_written: int = 0
    duplicate_chunks_skipped: int = 0
    error: str = ""


@dataclass
class OfficialPipelineSummary:
    documents_total: int
    documents_processed: int
    documents_failed: int
    pages_total: int
    pages_with_text: int
    pages_without_text: int
    chunks_written: int
    duplicate_chunks_skipped: int


def _safe_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return normalized[:100] or sha256(value.encode()).hexdigest()[:16]


def _section_heading(text: str) -> str:
    for raw_line in text.splitlines()[:20]:
        line = " ".join(raw_line.split()).strip(" -–—:;.")
        if 4 <= len(line) <= 120 and (
            line.isupper()
            or re.match(r"^(chapitre|section|partie|annexe|[0-9]+[.)])\b", line, re.I)
        ):
            return line
    return ""


def _extract_page(page) -> tuple[str, str]:
    try:
        return page.extract_text(extraction_mode="layout") or "", "layout"
    except Exception:
        return page.extract_text() or "", "plain"


def _load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [record for record in records if record.get("status") == "downloaded"]


def run_official_pdf_pipeline(
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "data/chunks_v2",
    max_tokens: int = 450,
    overlap_tokens: int = 75,
    minimum_page_characters: int = 80,
) -> OfficialPipelineSummary:
    raw_dir = Path(raw_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_dir / "manifest.json"
    records = _load_manifest(manifest_path)
    cleaner = FrenchMedicalCleaner()
    chunker = TokenChunker(
        min_tokens=100,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
    )
    temporary_chunks = output_dir / "chunks.jsonl.tmp"
    final_chunks = output_dir / "chunks.jsonl"
    quality_path = output_dir / "quality_report.json"
    seen_chunk_texts: set[str] = set()
    quality: list[DocumentQuality] = []

    with temporary_chunks.open("w", encoding="utf-8") as output:
        for position, record in enumerate(records, 1):
            pdf_path = raw_dir / record["filename"]
            document_quality = DocumentQuality(
                filename=record["filename"], title=record.get("title") or pdf_path.stem
            )
            try:
                reader = PdfReader(str(pdf_path))
                if reader.is_encrypted and not reader.decrypt(""):
                    raise ValueError("encrypted PDF requiring a password")
                document_quality.pages_total = len(reader.pages)
                document_id = _safe_id(pdf_path.stem)
                for page_number, page in enumerate(reader.pages, 1):
                    extracted, extraction_mode = _extract_page(page)
                    cleaned = cleaner.clean(extracted).strip()
                    if len(cleaned) < minimum_page_characters:
                        document_quality.pages_without_text += 1
                        continue
                    document_quality.pages_with_text += 1
                    section = _section_heading(cleaned)
                    page_source_id = f"{document_id}-p{page_number:04d}"
                    page_document = RawDocument(
                        source_id=page_source_id,
                        title=document_quality.title,
                        content=cleaned,
                        source_url=record["source_url"],
                        metadata={
                            "institution": "Ministère de la Santé et de la Protection Sociale",
                            "language": "fr",
                            "page_number": page_number,
                            "num_pages": len(reader.pages),
                            "document_id": document_id,
                            "local_filename": record["filename"],
                            "document_sha256": record.get("sha256", ""),
                            "section": section,
                            "extraction_mode": extraction_mode,
                        },
                    )
                    for chunk in chunker.chunk(page_document):
                        normalized = " ".join(chunk.text.casefold().split())
                        fingerprint = sha256(normalized.encode()).hexdigest()
                        if fingerprint in seen_chunk_texts:
                            document_quality.duplicate_chunks_skipped += 1
                            continue
                        seen_chunk_texts.add(fingerprint)
                        output.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
                        document_quality.chunks_written += 1
            except Exception as exc:
                document_quality.error = str(exc)
                logger.warning("Failed to process %s: %s", pdf_path.name, exc)
            quality.append(document_quality)
            logger.info(
                "[%d/%d] %s: pages=%d text=%d chunks=%d",
                position,
                len(records),
                pdf_path.name,
                document_quality.pages_total,
                document_quality.pages_with_text,
                document_quality.chunks_written,
            )

    temporary_chunks.replace(final_chunks)
    summary = OfficialPipelineSummary(
        documents_total=len(quality),
        documents_processed=sum(not item.error for item in quality),
        documents_failed=sum(bool(item.error) for item in quality),
        pages_total=sum(item.pages_total for item in quality),
        pages_with_text=sum(item.pages_with_text for item in quality),
        pages_without_text=sum(item.pages_without_text for item in quality),
        chunks_written=sum(item.chunks_written for item in quality),
        duplicate_chunks_skipped=sum(item.duplicate_chunks_skipped for item in quality),
    )
    quality_path.write_text(
        json.dumps(
            {"summary": asdict(summary), "documents": [asdict(item) for item in quality]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("Official PDF pipeline complete: %s", summary)
    return summary


if __name__ == "__main__":
    run_official_pdf_pipeline()
