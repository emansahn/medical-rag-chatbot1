"""
SentenceTransformerEmbedder — Indexation & Moteur RAG's `Embedder` implementation.

Uses a multilingual sentence-transformers model so French and Darija (once
transliterated) queries embed into the same space as the French source
corpus. Import of `sentence_transformers` stays inside `__init__`, not at
module level, so this file can sit in the repo without forcing the
dependency on anyone who isn't running `RAG_MODE=real`.
"""

from typing import List

from src.core.logging_config import get_logger
from src.rag.interfaces.embedder_interface import Embedder

logger = get_logger(__name__)


class SentenceTransformerEmbedder(Embedder):
    """Embeds text with a local sentence-transformers model."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()
        logger.info(
            "SentenceTransformerEmbedder loaded (model=%s, dim=%d)",
            model_name,
            self._dimension,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        vector = self._model.encode(
            [text], normalize_embeddings=True, show_progress_bar=False
        )
        return vector[0].tolist()

    @property
    def dimension(self) -> int:
        return self._dimension
