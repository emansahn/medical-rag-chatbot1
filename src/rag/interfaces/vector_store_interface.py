"""
Interface: Vector store & retrieval — Indexation & Moteur RAG's contract.

Wraps FAISS / ChromaDB / any other vector DB behind one interface so the
rest of the app never imports a vector-DB SDK directly.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from src.preprocessing.interfaces.document_loader_interface import DocumentChunk


@dataclass
class RetrievedChunk:
    """A chunk returned from similarity search, with its relevance score."""

    chunk: DocumentChunk
    score: float


class VectorStore(ABC):
    """Abstract base class for the vector index (FAISS, ChromaDB, ...)."""

    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        """Index a batch of chunks with their precomputed embeddings."""
        raise NotImplementedError

    @abstractmethod
    def similarity_search(self, query_embedding: List[float], top_k: int) -> List[RetrievedChunk]:
        """Return the `top_k` most relevant chunks for a query embedding,
        ranked by descending relevance score."""
        raise NotImplementedError

    @abstractmethod
    def is_ready(self) -> bool:
        """Whether the store has been built/populated and can serve queries.
        The backend's `/health` and `/status` endpoints surface this flag."""
        raise NotImplementedError


class Retriever(ABC):
    """Higher-level retrieval interface, combining an Embedder + VectorStore,
    and optionally query rewriting / re-ranking."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> List[RetrievedChunk]:
        """Return the most relevant chunks for a natural-language query."""
        raise NotImplementedError
