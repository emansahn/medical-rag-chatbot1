"""
Interface: Embeddings — PERSON 2's contract.

Any embedding backend (SentenceTransformers, OpenAI embeddings, HuggingFace
Inference API...) must implement this interface. The rest of the RAG
pipeline (`VectorStore`, `Retriever`) only depends on `Embedder`, never on a
specific model — swapping models later means writing one new class, nothing else.
"""
from abc import ABC, abstractmethod
from typing import List


class Embedder(ABC):
    """Abstract base class for turning text into vectors."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of document chunks. Returns one vector per input text."""
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single user query. Kept separate from `embed_documents`
        because some models use asymmetric query/document embeddings."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality produced by this embedder (needed to configure
        the vector store index)."""
        raise NotImplementedError
