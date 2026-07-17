"""
SimpleRetriever — Person 2's `Retriever` implementation.

Combines an `Embedder` and a `VectorStore` with no query rewriting or
re-ranking: embed the query, search the store. Kept as its own class (rather
than inlined in `RealRAGService`) so a future re-ranking or query-rewriting
retriever can be swapped in without touching `RealRAGService`.
"""

from typing import List

from src.core.exceptions import RetrievalError
from src.core.logging_config import get_logger
from src.rag.interfaces.embedder_interface import Embedder
from src.rag.interfaces.vector_store_interface import (
    RetrievedChunk,
    Retriever,
    VectorStore,
)

logger = get_logger(__name__)


class SimpleRetriever(Retriever):
    """Embeds the query then runs a similarity search against the vector store."""

    def __init__(self, embedder: Embedder, vector_store: VectorStore) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int) -> List[RetrievedChunk]:
        query = query.strip()
        if not query:
            raise RetrievalError("Cannot retrieve for an empty query.")
        try:
            query_embedding = self.embedder.embed_query(query)
            return self.vector_store.similarity_search(query_embedding, top_k)
        except RetrievalError:
            raise
        except Exception as exc:  # pragma: no cover - defensive, wraps backend errors
            logger.exception("Retrieval failed for query: %r", query)
            raise RetrievalError(f"Retrieval failed: {exc}") from exc
