"""
Interface: RAGService — PERSON 2's real contract with the rest of the app.

This is the ONLY thing the backend depends on. It has zero knowledge of
FAISS, ChromaDB, LangChain, or sentence-transformers — those are
implementation details that live behind this interface, inside whichever
concrete class is injected (`MockRAGService` today, `RealRAGService` once
Person 2 finishes).

Because of this, `pip install -r requirements/backend.txt` (no RAG libraries
at all) is enough to run the full backend against the mock implementation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class SourceCitation:
    """A single source shown under an assistant message in the UI."""

    title: str
    url: str
    excerpt: str


@dataclass
class RAGAnswer:
    """The full result of a RAG query, consumed by the backend's chat service."""

    answer: str
    sources: List[SourceCitation] = field(default_factory=list)
    is_mock: bool = True


class RAGService(ABC):
    """Abstract base class every RAG engine implementation must satisfy."""

    @abstractmethod
    def answer_question(self, question: str, language: str = "fr") -> RAGAnswer:
        """Answer a medical question, grounded in retrieved sources.

        Args:
            question: The user's question (already translated to French if
                Darija support is enabled and Person 2's translator ran).
            language: Target response language ("fr" or "ary" for Darija).
        """
        raise NotImplementedError

    @abstractmethod
    def is_ready(self) -> bool:
        """Whether this is a fully-functional, production-grade engine
        (False for the mock, True once the real engine is indexed and live).
        Surfaced by the `/status` endpoint and the frontend's status badge."""
        raise NotImplementedError
