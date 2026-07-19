"""Unit tests for SimpleRetriever, using fake Embedder/VectorStore doubles
so no sentence-transformers/chromadb model needs to load."""

from typing import List

import pytest

from src.core.exceptions import RetrievalError
from src.preprocessing.interfaces.document_loader_interface import DocumentChunk
from src.rag.interfaces.embedder_interface import Embedder
from src.rag.interfaces.vector_store_interface import RetrievedChunk, VectorStore
from src.rag.retrievers.simple_retriever import SimpleRetriever


class _FakeEmbedder(Embedder):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[1.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return [1.0, 0.0]

    @property
    def dimension(self) -> int:
        return 2


class _FakeVectorStore(VectorStore):
    def __init__(self, results: List[RetrievedChunk]):
        self._results = results

    def add_chunks(self, chunks, embeddings) -> None:
        raise NotImplementedError

    def similarity_search(
        self, query_embedding: List[float], top_k: int
    ) -> List[RetrievedChunk]:
        return self._results[:top_k]

    def is_ready(self) -> bool:
        return bool(self._results)


def _make_results(n: int) -> List[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk=DocumentChunk(
                chunk_id=f"c{i}",
                text=f"texte {i}",
                source_id="s1",
                source_title="titre",
                source_url="https://example.ma",
            ),
            score=1.0 - i * 0.1,
        )
        for i in range(n)
    ]


def test_retrieve_returns_expected_top_k_count():
    store = _FakeVectorStore(_make_results(5))
    retriever = SimpleRetriever(_FakeEmbedder(), store)

    results = retriever.retrieve("Quels sont les symptômes de la grippe ?", top_k=3)

    assert len(results) == 3


def test_retrieve_returns_fewer_results_than_top_k_when_store_is_smaller():
    store = _FakeVectorStore(_make_results(2))
    retriever = SimpleRetriever(_FakeEmbedder(), store)

    results = retriever.retrieve("question", top_k=5)

    assert len(results) == 2


def test_retrieve_rejects_empty_query():
    retriever = SimpleRetriever(_FakeEmbedder(), _FakeVectorStore(_make_results(1)))

    with pytest.raises(RetrievalError):
        retriever.retrieve("   ", top_k=3)


def test_retrieve_reranks_exact_medical_terms_over_slightly_higher_vector_score():
    results = _make_results(2)
    results[0].chunk.text = "Organisation générale du programme tuberculose."
    results[0].score = 0.78
    results[1].chunk.text = "La vaccination BCG est administrée aux nouveau-nés."
    results[1].score = 0.70
    retriever = SimpleRetriever(_FakeEmbedder(), _FakeVectorStore(results))

    ranked = retriever.retrieve("recommandations vaccination BCG", top_k=1)

    assert ranked[0].chunk.chunk_id == "c1"
