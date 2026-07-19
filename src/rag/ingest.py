"""
src/rag/ingest.py — Indexation & Moteur RAG's ingestion script.

Reads chunks via `get_chunk_provider()` (so it runs against Person 1's mock
data before their real pipeline lands, and against real data once it does),
embeds them, and populates the vector store.

Usage (from the project root, so `src...` imports resolve):
    python -m src.rag.ingest
"""

from src.core.config import settings
from src.core.logging_config import get_logger
from src.preprocessing.container import get_chunk_provider


def main() -> None:
    logger = get_logger(__name__)

    chunks = get_chunk_provider().list_chunks()
    if not chunks:
        raise SystemExit(
            "No production chunks are available. Run the preprocessing pipeline first."
        )

    from src.rag.embedders.sentence_transformer_embedder import (
        SentenceTransformerEmbedder,
    )
    from src.rag.vector_stores.chroma_store import ChromaVectorStore

    logger.info(
        "Embedding %d chunks with %s ...", len(chunks), settings.embedding_model_name
    )
    embedder = SentenceTransformerEmbedder(settings.embedding_model_name)
    embeddings = embedder.embed_documents([chunk.text for chunk in chunks])

    store = ChromaVectorStore(settings.vector_store_path)
    store.add_chunks(chunks, embeddings)
    logger.info("Indexed %d chunks into %s", len(chunks), settings.vector_store_path)


if __name__ == "__main__":
    main()
