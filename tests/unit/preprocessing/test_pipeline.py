"""Unit tests for run_pipeline (src/preprocessing/pipeline.py).

Filesystem access is fully isolated via `tmp_path`; real loaders (PDF/web)
are replaced with a fake `DocumentLoader` returning canned `RawDocument`s so
these tests never touch data/raw, data/processed, data/chunks, or the network.
"""
import json
import logging
from pathlib import Path
from typing import List

import pytest

from src.preprocessing.chunking.token_chunker import TokenChunker
from src.preprocessing.cleaning.french_medical_cleaner import FrenchMedicalCleaner
from src.preprocessing.interfaces.document_loader_interface import DocumentLoader, RawDocument, TextCleaner
from src.preprocessing.pipeline import PipelineSummary, run_pipeline


class _FakeLoader(DocumentLoader):
    def __init__(self, documents: List[RawDocument]) -> None:
        self._documents = documents

    def load(self) -> List[RawDocument]:
        return list(self._documents)


class _FakeCleaner(TextCleaner):
    """Passes text through unchanged (stripped), but raises for any text
    containing a poison marker -- simulates a document failing to clean."""

    POISON_MARKER = "__POISON__"

    def clean(self, raw_text: str) -> str:
        if self.POISON_MARKER in raw_text:
            raise ValueError("simulated cleaning failure")
        return raw_text.strip()


def _make_documents() -> List[RawDocument]:
    return [
        RawDocument(
            source_id="diabete-guide",
            title="Guide du diabete",
            content="Le diabete de type 2 peut etre prevenu par une bonne hygiene de vie.",
            source_url="https://example.org/diabete",
            metadata={"institution": "Ministere de la Sante", "language": "fr"},
        ),
        RawDocument(
            source_id="vaccination-guide",
            title="Calendrier de vaccination",
            content="La vaccination protege contre les maladies infectieuses.",
            source_url="https://example.org/vaccination",
            metadata={"institution": "OMS Maroc", "language": "fr"},
        ),
    ]


def test_pipeline_writes_processed_json_and_chunks_jsonl(tmp_path: Path):
    documents = _make_documents()
    processed_dir = tmp_path / "processed"
    chunks_dir = tmp_path / "chunks"

    summary = run_pipeline(
        loaders=[_FakeLoader(documents)],
        cleaner=FrenchMedicalCleaner(),
        chunker=TokenChunker(),
        processed_dir=processed_dir,
        chunks_dir=chunks_dir,
    )

    assert isinstance(summary, PipelineSummary)
    assert summary.documents_processed == 2
    assert summary.documents_skipped == 0
    assert summary.chunks_generated == 2  # one short chunk per short document

    diabete_json = json.loads((processed_dir / "diabete-guide.json").read_text(encoding="utf-8"))
    assert diabete_json["source_id"] == "diabete-guide"
    assert diabete_json["title"] == "Guide du diabete"
    assert diabete_json["source_url"] == "https://example.org/diabete"
    assert "diabete de type 2" in diabete_json["content"]

    vaccination_json = json.loads((processed_dir / "vaccination-guide.json").read_text(encoding="utf-8"))
    assert vaccination_json["source_id"] == "vaccination-guide"

    chunk_lines = (chunks_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(chunk_lines) == 2
    chunk_records = [json.loads(line) for line in chunk_lines]
    assert {record["source_id"] for record in chunk_records} == {"diabete-guide", "vaccination-guide"}
    for record in chunk_records:
        assert record["chunk_id"]
        assert record["text"]
        assert record["source_title"]
        assert record["source_url"]


def test_pipeline_skips_document_that_fails_cleaning(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    good_document = _make_documents()[0]
    poisoned_document = RawDocument(
        source_id="broken-doc",
        title="Document casse",
        content=f"Contenu {_FakeCleaner.POISON_MARKER} illisible",
        source_url="https://example.org/broken",
        metadata={},
    )

    with caplog.at_level(logging.WARNING, logger="src.preprocessing.pipeline"):
        summary = run_pipeline(
            loaders=[_FakeLoader([good_document, poisoned_document])],
            cleaner=_FakeCleaner(),
            chunker=TokenChunker(),
            processed_dir=tmp_path / "processed",
            chunks_dir=tmp_path / "chunks",
        )

    assert summary.documents_processed == 1
    assert summary.documents_skipped == 1
    assert any("broken-doc" in record.message for record in caplog.records)

    processed_files = list((tmp_path / "processed").glob("*.json"))
    assert len(processed_files) == 1
    assert processed_files[0].name == "diabete-guide.json"


def test_pipeline_with_no_documents_completes_without_error(tmp_path: Path):
    processed_dir = tmp_path / "processed"
    chunks_dir = tmp_path / "chunks"

    summary = run_pipeline(loaders=[_FakeLoader([])], processed_dir=processed_dir, chunks_dir=chunks_dir)

    assert summary == PipelineSummary(documents_processed=0, documents_skipped=0, chunks_generated=0)
    assert list(processed_dir.glob("*.json")) == []
    assert (chunks_dir / "chunks.jsonl").read_text(encoding="utf-8") == ""
