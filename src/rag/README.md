# `src/rag/` — Person 2's workspace

**Goal:** turn Person 1's chunks into an indexed vector store, retrieve
relevant chunks for a question, and generate a grounded answer.

**Install only:** `pip install -r requirements/person2-rag.txt -r requirements/backend.txt -r requirements/dev.txt`.

## What already exists (do not need to touch)

- `interfaces/embedder_interface.py`, `vector_store_interface.py`,
  `llm_interface.py` — internal building blocks (`Embedder`, `VectorStore`,
  `Retriever`, `PromptBuilder`, `LLMClient`).
- `interfaces/rag_service_interface.py` — the **app-facing** contract:
  `RAGService.answer_question()` / `.is_ready()`. This is the only thing the
  backend depends on.
- `services/mock_rag_service.py` — a complete, dependency-free fake engine.
  This is why the app is demoable today without your engine finished.
- `services/real_rag_service.py` — your integration point (see below);
  has a commented template showing exactly how to wire your components in.
- `container.py` — reads `RAG_MODE` from `.env` and returns Mock or Real.
  You never edit this file.

## What you build here

```
src/rag/
├── embedders/
│   └── sentence_transformer_embedder.py   # class SentenceTransformerEmbedder(Embedder)
├── vector_stores/
│   └── chroma_store.py                    # class ChromaVectorStore(VectorStore)
├── retrievers/
│   └── simple_retriever.py                # class SimpleRetriever(Retriever)
├── prompting/
│   └── medical_prompt_builder.py          # class MedicalPromptBuilder(PromptBuilder)
├── llm/
│   └── openai_client.py                   # class OpenAILLMClient(LLMClient)
└── ingest.py                              # chunks (via get_chunk_provider()) -> embeddings -> vector store
```

## Contract you must respect

1. `Embedder.embed_documents/embed_query` return plain `list[float]` vectors.
2. `VectorStore.add_chunks` accepts `DocumentChunk` objects exactly as
   produced by Person 1's pipeline — read them via
   `src.preprocessing.container.get_chunk_provider()` so your ingestion
   script works against Person 1's mock data too, before their real
   pipeline is done.
3. `PromptBuilder.build()` must instruct the LLM to answer **only** from the
   provided context and say so explicitly when context is insufficient —
   this is the project's core anti-hallucination requirement.
4. `RealRAGService.is_ready()` must return `True` only once the vector store
   is actually populated — the `/status` endpoint and frontend badge rely on
   this being accurate, not always-true.

## Activating your real engine

```bash
# .env
RAG_MODE=real
```
Restart the backend. If `RealRAGService.__init__` isn't implemented yet,
you'll get a clear `NotImplementedError` — that's intentional, not a bug.

## Testing

`tests/unit/rag/` (create this folder). At minimum: retrieval returns the
expected top-k count; the prompt builder degrades gracefully with zero
retrieved chunks.

## You do NOT need to touch

`src/backend/`, `src/frontend/`, `src/preprocessing/`, `src/analytics/`.
