"""Unit tests for ChromaVectorStore. Uses a temp directory and hand-crafted
vectors — no sentence-transformers model, no network."""

from src.preprocessing.interfaces.document_loader_interface import DocumentChunk
from src.rag.vector_stores.chroma_store import ChromaVectorStore


def _chunk(chunk_id: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        text=f"contenu de {chunk_id}",
        source_id="doc-1",
        source_title="Guide de prévention",
        source_url="https://www.sante.gov.ma/guide",
        metadata={"theme": "prevention"},
    )


def test_store_is_not_ready_when_empty(tmp_path):
    store = ChromaVectorStore(str(tmp_path))
    assert store.is_ready() is False
    assert store.similarity_search([1.0, 0.0], top_k=3) == []


def test_add_chunks_then_search_returns_closest_match(tmp_path):
    store = ChromaVectorStore(str(tmp_path))
    chunks = [_chunk("c1"), _chunk("c2")]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]

    store.add_chunks(chunks, embeddings)

    assert store.is_ready() is True
    results = store.similarity_search([1.0, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "c1"
    assert results[0].chunk.metadata == {"theme": "prevention"}
    assert results[0].score > 0.99  # identical vector -> cosine similarity ~1


def test_add_chunks_with_empty_list_is_a_no_op(tmp_path):
    store = ChromaVectorStore(str(tmp_path))
    store.add_chunks([], [])
    assert store.is_ready() is False
