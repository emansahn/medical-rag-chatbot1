"""
SimpleRetriever — Indexation & Moteur RAG's `Retriever` implementation.

Combines an `Embedder` and a `VectorStore`, then applies a lightweight lexical
re-ranking over semantic candidates. Kept as its own class (rather
than inlined in `RealRAGService`) so a future re-ranking or query-rewriting
retriever can be swapped in without touching `RealRAGService`.
"""

import re
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

_FRENCH_STOPWORDS = {
    "aux", "avec", "contre", "dans", "des", "est", "les", "pour", "que",
    "quelles", "sont", "sur", "une",
}


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
            candidate_k = max(100, top_k * 20)
            candidates = self.vector_store.similarity_search(
                query_embedding, candidate_k
            )
            ranked = sorted(
                candidates,
                key=lambda item: self._hybrid_score(query, item),
                reverse=True,
            )
            return ranked[:top_k]
        except RetrievalError:
            raise
        except Exception as exc:  # pragma: no cover - defensive, wraps backend errors
            logger.exception("Retrieval failed for query: %r", query)
            raise RetrievalError(f"Retrieval failed: {exc}") from exc

    @staticmethod
    def _hybrid_score(query: str, item: RetrievedChunk) -> float:
        raw_terms = re.findall(r"[\wÀ-ÿ]+", query)
        weighted_terms = {
            term.casefold(): 3.0 if term.isupper() and len(term) >= 2 else 1.0
            for term in raw_terms
            if len(term) >= 3 and term.casefold() not in _FRENCH_STOPWORDS
        }
        if not weighted_terms:
            return item.score
        haystack = f"{item.chunk.source_title} {item.chunk.text}".casefold()
        matched = sum(
            weight for term, weight in weighted_terms.items() if term in haystack
        )
        lexical_coverage = matched / sum(weighted_terms.values())
        return (0.55 * item.score) + (0.45 * lexical_coverage)
