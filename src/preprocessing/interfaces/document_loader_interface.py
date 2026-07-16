"""
Interface: Document collection & loading — PERSON 1's contract.

Person 1 implements concrete classes that inherit from `DocumentLoader` for
each data source (Ministère de la Santé PDFs, OMS Maroc web pages, CHU guides...).

The rest of the application (Person 2's ingestion pipeline, and any future
admin tooling) only ever depends on this abstract interface, never on a
specific loader. This means Person 1 can add/change loaders freely without
breaking anything downstream.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class RawDocument:
    """A single document before cleaning/chunking.

    Attributes:
        source_id: Stable unique identifier (e.g. filename or URL slug).
        title: Human-readable title, used later for source citation in the UI.
        content: Raw extracted text (may still contain noise/boilerplate).
        source_url: Original URL or file path, shown to the user as a citation.
        metadata: Free-form extra info (publish date, institution, language...).
    """

    source_id: str
    title: str
    content: str
    source_url: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentLoader(ABC):
    """Abstract base class every Person-1 loader must implement."""

    @abstractmethod
    def load(self) -> List[RawDocument]:
        """Fetch and return raw documents from this source.

        Must NOT perform cleaning or chunking — only extraction. Cleaning
        belongs in `TextCleaner`, chunking in `TextChunker` (see
        `chunking_interface.py`... to be implemented by Person 1 following
        the same pattern as this file).
        """
        raise NotImplementedError


class TextCleaner(ABC):
    """Abstract base class for text normalization/cleaning steps."""

    @abstractmethod
    def clean(self, raw_text: str) -> str:
        """Remove boilerplate (headers/footers/menus), normalize whitespace,
        fix encoding artifacts, etc. Must be deterministic and side-effect free."""
        raise NotImplementedError


class TextChunker(ABC):
    """Abstract base class for splitting cleaned text into retrieval-ready chunks."""

    @abstractmethod
    def chunk(self, document: RawDocument) -> List["DocumentChunk"]:
        """Split a cleaned document into 300-800 token chunks with overlap,
        as specified in the project brief."""
        raise NotImplementedError


@dataclass
class DocumentChunk:
    """The final unit that Person 2 will embed and index.

    This is the hand-off contract between Person 1 and Person 2: Person 1's
    pipeline must produce a list of these, Person 2's ingestion code
    consumes exactly this shape (see `src/rag/interfaces/vector_store_interface.py`).
    """

    chunk_id: str
    text: str
    source_id: str
    source_title: str
    source_url: str
    metadata: dict[str, Any] = field(default_factory=dict)
