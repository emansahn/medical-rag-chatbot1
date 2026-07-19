"""
Interface: RAGService — Indexation & Moteur RAG's real contract with the rest of the app.

This is the ONLY thing the backend depends on. It has zero knowledge of
FAISS, ChromaDB, LangChain, or sentence-transformers — those are
implementation details that live behind this interface, inside whichever
concrete production class is injected. Tests use small local doubles without
introducing a fake runtime mode in the application.
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
    is_mock: bool = False


class RAGService(ABC):
    """Abstract base class every RAG engine implementation must satisfy."""

    @abstractmethod
    def answer_question(self, question: str, language: str = "fr") -> RAGAnswer:
        """Answer a medical question, grounded in retrieved sources.

        Args:
            question: The user's original question. The real service translates
                Darija internally for retrieval while preserving this text.
            language: Target response language and script.
        """
        raise NotImplementedError

    @abstractmethod
    def is_ready(self) -> bool:
        """Whether the production engine is indexed and ready."""
        raise NotImplementedError
