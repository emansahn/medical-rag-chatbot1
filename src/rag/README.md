# `src/rag/` — Indexation & Moteur RAG

**Goal:** turn ingested chunks into an indexed vector store, retrieve
relevant chunks for a question, and generate a grounded answer.

**Install:** `pip install -r requirements/person2-rag.txt -r requirements/backend.txt -r requirements/dev.txt`.

## Structure

- `interfaces/` — internal contracts (`Embedder`, `VectorStore`, `Retriever`,
  `PromptBuilder`, `LLMClient`) and the app-facing `RAGService` contract
  (`answer_question()` / `is_ready()`) that `src/backend/` depends on.
- `embedders/sentence_transformer_embedder.py` — `SentenceTransformerEmbedder(Embedder)`.
- `vector_stores/chroma_store.py` — `ChromaVectorStore(VectorStore)`.
- `retrievers/simple_retriever.py` — `SimpleRetriever(Retriever)`.
- `prompting/medical_prompt_builder.py` — `MedicalPromptBuilder(PromptBuilder)`,
  enforces the anti-hallucination rule: answer only from context, say so
  explicitly when the context is insufficient.
- `llm/ollama_client.py` — `OllamaLLMClient(LLMClient)`, talks to a local
  Ollama server, no API key required (default, `LLM_PROVIDER=ollama`).
- `llm/openai_client.py` — `OpenAILLMClient(LLMClient)`, alternative backend
  (`LLM_PROVIDER=openai`, requires `LLM_API_KEY`).
- `services/mock_rag_service.py` — dependency-free fake engine used when
  `RAG_MODE=mock` (default), so the rest of the app is demoable without any
  of this module installed.
- `services/real_rag_service.py` — wires the components above; used when
  `RAG_MODE=real`.
- `container.py` — reads `RAG_MODE` from `.env` and returns Mock or Real.
- `ingest.py` — chunks (via `get_chunk_provider()`) → embeddings → vector store.

## Activating the real engine

```bash
# .env
RAG_MODE=real
LLM_PROVIDER=ollama   # or openai
```

Run `python -m src.rag.ingest` to populate the vector store, then restart
the backend.

## Testing

`tests/unit/rag/` covers the retriever, the ChromaDB store, the prompt
builder, and both LLM clients.
