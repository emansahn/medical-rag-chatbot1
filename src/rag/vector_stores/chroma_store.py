"""
ChromaVectorStore — Person 2's `VectorStore` implementation.

Wraps a persistent ChromaDB collection. `chromadb` is imported lazily inside
`__init__` so this file can exist in the repo without forcing the dependency
on anyone running in `RAG_MODE=mock`.

Chroma's metadata values must be flat scalars (str/int/float/bool), so
`DocumentChunk.metadata` (a free-form dict) is serialized to JSON under a
single key and rehydrated on read.
"""

import json
from typing import List

from src.core.logging_config import get_logger
from src.preprocessing.interfaces.document_loader_interface import DocumentChunk
from src.rag.interfaces.vector_store_interface import RetrievedChunk, VectorStore

logger = get_logger(__name__)

_COLLECTION_NAME = "medical_chunks"
_EXTRA_METADATA_KEY = "_metadata_json"


class ChromaVectorStore(VectorStore):
    """Persistent ChromaDB-backed vector index, cosine similarity."""

    def __init__(self, persist_path: str) -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=persist_path)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaVectorStore ready (path=%s, existing_count=%d)",
            persist_path,
            self._collection.count(),
        )

    def add_chunks(
        self, chunks: List[DocumentChunk], embeddings: List[List[float]]
    ) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[self._to_chroma_metadata(chunk) for chunk in chunks],
        )
        logger.info("Indexed %d chunks into ChromaDB", len(chunks))

    def similarity_search(
        self, query_embedding: List[float], top_k: int
    ) -> List[RetrievedChunk]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
        )
        chunks = results["documents"][0]
        metadatas = results["metadatas"][0]
        ids = results["ids"][0]
        distances = results["distances"][0]

        retrieved = []
        for chunk_id, text, metadata, distance in zip(
            ids, chunks, metadatas, distances
        ):
            retrieved.append(
                RetrievedChunk(
                    chunk=self._from_chroma_metadata(chunk_id, text, metadata),
                    score=1.0
                    - distance,  # cosine space: distance = 1 - cosine_similarity
                )
            )
        return retrieved

    def is_ready(self) -> bool:
        return self._collection.count() > 0

    @staticmethod
    def _to_chroma_metadata(chunk: DocumentChunk) -> dict:
        return {
            "source_id": chunk.source_id,
            "source_title": chunk.source_title,
            "source_url": chunk.source_url,
            _EXTRA_METADATA_KEY: json.dumps(chunk.metadata, ensure_ascii=False),
        }

    @staticmethod
    def _from_chroma_metadata(
        chunk_id: str, text: str, metadata: dict
    ) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=chunk_id,
            text=text,
            source_id=metadata.get("source_id", ""),
            source_title=metadata.get("source_title", ""),
            source_url=metadata.get("source_url", ""),
            metadata=json.loads(metadata.get(_EXTRA_METADATA_KEY, "{}")),
        )
