# Developer Guide

## Coding standards

- **PEP8**, enforced via `ruff`/`black` (`black src/ tests/`, `ruff check src/`).
- **Type hints everywhere.**
- Prefer **dataclasses / Pydantic models** over loose dicts across module boundaries.
- No `print()` — use `from src.core.logging_config import get_logger`.
- Raise typed exceptions from `src/core/exceptions.py`.
- **Never instantiate a concrete `Mock*`/`Real*` class outside its own
  `container.py`.** If you find yourself writing `MockRAGService()` in a
  router, service, or frontend page, that's a coupling bug — depend on
  `get_rag_service()` (or the `RAGService` type) instead.

## The Mock/Real/Container pattern (read this before writing anything)

Every cross-team boundary in this repo follows the same three-part pattern:

1. **Interface** (`*/interfaces/*.py`) — an `ABC` with the methods the rest
   of the app needs. Zero external dependencies.
2. **Implementations** — `Mock*` (dependency-free, sample data, always
   available) and `Real*` (the actual work, imports heavy libraries lazily).
3. **Container** (`*/container.py`) — reads a `*_MODE` env var, builds and
   caches the right implementation, exposes a `get_*()` function used as a
   FastAPI `Depends(...)` target (or called directly from Streamlit/scripts).

This is why the app always boots: routers and pages only ever import the
interface type and the container's `get_*()` function.

## How Person 1 integrates

1. Implement `DocumentLoader`, `TextCleaner`, `TextChunker`
   (`src/preprocessing/interfaces/document_loader_interface.py`) in new
   files under `src/preprocessing/loaders/`, `cleaning/`, `chunking/`.
2. Orchestrate them in `src/preprocessing/pipeline.py`, writing
   `DocumentChunk`s to `data/chunks/` (JSONL) and `RawDocument`s to
   `data/processed/` (JSON).
3. Fill in `RealDocumentProvider`/`RealChunkProvider`/`RealDatasetLoader`
   in `src/preprocessing/providers/real_providers.py` (skeleton already
   reads from those paths — confirm the field names match your output).
4. Test locally with `DATA_MODE=real` in `.env`.
5. Do not touch `src/backend/`, `src/frontend/`, `src/rag/`.

## How Indexation & Moteur RAG integrates

1. Implement `Embedder`, `VectorStore`, `Retriever`, `PromptBuilder`,
   `LLMClient` (`src/rag/interfaces/`) in new files under
   `src/rag/embedders/`, `vector_stores/`, `retrievers/`, `prompting/`, `llm/`.
2. Write `src/rag/ingest.py`: read chunks (via `get_chunk_provider()`, so it
   already works against Person 1's mock or real data), embed them, populate
   your vector store.
3. Fill in `src/rag/services/real_rag_service.py` using those components
   (a commented template is at the bottom of that file already).
4. Test locally with `RAG_MODE=real` in `.env`.
5. Do not touch `src/backend/`, `src/frontend/`, `src/preprocessing/`.

## How Person 3's layers fit together

```
Router (HTTP)  →  Service (business logic)  →  Container → Interface  →  Mock/Real impl
```

- Routers (`src/backend/api/routers/*.py`) only parse/validate input and
  call a service.
- Services (`src/backend/services/*.py`) hold the logic and depend on
  interfaces (`RAGService`), unit-tested without an HTTP server.
- `src/backend/api/dependencies.py` and `src/rag/container.py` /
  `src/preprocessing/container.py` are the only places concrete
  implementations get constructed.

## Adding a new backend endpoint

1. Add a Pydantic schema in `src/backend/schemas/`.
2. Add business logic in a service in `src/backend/services/` (depend on
   interfaces, not concrete classes).
3. Add a route in `src/backend/api/routers/`, register it in `src/backend/main.py`.
4. Add an integration test in `tests/integration/`.

## Adding a new Streamlit page

1. Create `src/frontend/pages/N_Name.py`.
2. Call `apply_theme(...)` first, then `render_sidebar()`.
3. Use `get_backend_client()` for backend calls — never call `requests` directly.

## Switching modes locally

```bash
# .env
RAG_MODE=mock     # or real, once you've implemented RealRAGService
DATA_MODE=mock    # or real, once you've implemented the real providers
```

Restart `uvicorn` after changing `.env` — settings are loaded once at startup.

See `docs/collaboration_workflow.md` for git branching, PR review rules,
and the full integration/testing process.
