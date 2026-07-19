"""
Real data providers — PERSON 1 implements these.

Reads from `data/chunks/` (and `data/processed/`) once your pipeline
(`src/preprocessing/pipeline.py`, which you create) has populated them.
Heavy parsing libraries stay inside your loaders/cleaners, not here — this
file should stay a thin "read what's on disk" layer.
"""
import json
from pathlib import Path
from typing import List

from src.core.config import settings
from src.preprocessing.interfaces.data_provider_interface import ChunkProvider, Dataset, DatasetLoader, DocumentProvider
from src.preprocessing.interfaces.document_loader_interface import DocumentChunk, RawDocument

_PROCESSED_PATH = Path("data/processed")


class RealDocumentProvider(DocumentProvider):
    """TODO(Person 1): confirm this matches the file format your pipeline writes."""

    def list_documents(self) -> List[RawDocument]:
        documents = []
        for file in _PROCESSED_PATH.glob("*.json"):
            data = json.loads(file.read_text(encoding="utf-8"))
            documents.append(RawDocument(**data))
        return documents

    def count(self) -> int:
        return len(list(_PROCESSED_PATH.glob("*.json")))


class RealChunkProvider(ChunkProvider):
    """TODO(Person 1): confirm this matches the JSONL format your chunker writes."""

    def list_chunks(self) -> List[DocumentChunk]:
        chunks = []
        chunks_path = Path(settings.chunks_path)
        for file in sorted(chunks_path.glob("*.jsonl")):
            with file.open(encoding="utf-8") as lines:
                for line in lines:
                    if line.strip():
                        chunks.append(DocumentChunk(**json.loads(line)))
        return chunks

    def count(self) -> int:
        return len(self.list_chunks())


class RealDatasetLoader(DatasetLoader):
    def load(self) -> Dataset:
        return Dataset(
            documents=RealDocumentProvider().list_documents(),
            chunks=RealChunkProvider().list_chunks(),
        )
