"""
Interfaces: DocumentProvider, ChunkProvider, DatasetLoader — PERSON 1's
app-facing contract.

Distinct from `document_loader_interface.py`, which defines the *internal*
building blocks Person 1 uses inside their own pipeline (`DocumentLoader`,
`TextCleaner`, `TextChunker`). These three interfaces are what the REST of
the application (analytics dashboard, ingestion scripts, future admin tools)
is allowed to depend on — never on Person 1's loaders/cleaners directly.

Each has a Mock implementation (`src/preprocessing/providers/mock_providers.py`)
returning small, realistic sample data, so anything built against these
interfaces works today without Person 1 having collected a single real
document yet.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from src.preprocessing.interfaces.document_loader_interface import DocumentChunk, RawDocument


class DocumentProvider(ABC):
    """Provides the current set of raw/cleaned source documents."""

    @abstractmethod
    def list_documents(self) -> List[RawDocument]:
        """Return all currently available source documents."""
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Return how many documents are available (used by /status and the dashboard)."""
        raise NotImplementedError


class ChunkProvider(ABC):
    """Provides the current set of retrieval-ready chunks (the Indexation & Moteur RAG engine consumes this)."""

    @abstractmethod
    def list_chunks(self) -> List[DocumentChunk]:
        """Return all currently available chunks."""
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Return how many chunks are available."""
        raise NotImplementedError


class DatasetLoader(ABC):
    """Higher-level facade combining document + chunk loading for scripts/dashboards
    that just want "give me the dataset" without caring about the two-stage split."""

    @abstractmethod
    def load(self) -> "Dataset":
        raise NotImplementedError


@dataclass
class Dataset:
    documents: List[RawDocument] = field(default_factory=list)
    chunks: List[DocumentChunk] = field(default_factory=list)
