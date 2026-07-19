# Architecture

## Core principle: dependency inversion, not just folder separation

The previous structure already split code by owner, but the *dependency
graph* was wrong: the backend and frontend transitively required FAISS,
ChromaDB, LangChain, and sentence-transformers just to boot — because
`requirements.txt` installed everything for everyone, and nothing stood
between the API layer and a concrete RAG implementation.

This refactor fixes the actual coupling, not just where files live:

```
Router/Frontend  →  Interface (RAGService / DocumentProvider / ...)  →  Mock impl (default) or Real impl (opt-in)
```

Person 3's code (and Person 1's, and the analytics dashboard) depends
**only on interfaces**. Concrete implementations are chosen at runtime by
two environment variables, never hardcoded:

- `RAG_MODE=mock|real` → selects `MockRAGService` or `RealRAGService`
- `DATA_MODE=mock|real` → selects Mock or Real `DocumentProvider`/`ChunkProvider`/`DatasetLoader`

Both default to `mock`. **The application always boots successfully in
mock mode**, with zero RAG or scraping libraries installed.

## Folder structure

```
medical-rag-chatbot/
├── requirements/              # Split, per-owner dependency files (see requirements/README.md)
├── data/
│   ├── raw/ processed/ chunks/   # Person 1's output
│   ├── vector_store/               # Indexation & Moteur RAG's index
│   └── analytics/                    # Generated CSVs for Power BI
├── docs/                       # This documentation set
├── tests/
│   ├── unit/                    # Fast, isolated, no server/network
│   └── integration/               # FastAPI TestClient tests
└── src/
    ├── core/                      # config, logging, exceptions, security placeholder (Person 3)
    ├── preprocessing/              # PERSON 1
    │   ├── interfaces/               # document_loader_interface.py (internal building blocks)
    │   │                              #   + data_provider_interface.py (app-facing contract)
    │   ├── providers/                 # mock_providers.py (default) / real_providers.py (Person 1 fills in)
    │   └── container.py                # DI switch, reads DATA_MODE
    ├── rag/                        # INDEXATION & MOTEUR RAG
    │   ├── interfaces/               # embedder/vector_store/llm interfaces (internal)
    │   │                              #   + rag_service_interface.py (app-facing contract: RAGService)
    │   ├── services/                  # mock_rag_service.py (default) / real_rag_service.py
    │   └── container.py                # DI switch, reads RAG_MODE
    ├── analytics/                  # PERSON 3 — sample data generator + CSV export for Power BI
    ├── admin/                      # SQLite glossary workflow, admin auth, sessions and audit
    ├── backend/                    # PERSON 3 — FastAPI REST API
    │   ├── api/
    │   │   ├── routers/               # chat, health, status, config, analytics
    │   │   └── dependencies.py         # THE ONLY place concrete services are constructed
    │   ├── schemas/                    # Pydantic request/response models
    │   ├── services/                    # Business logic (ChatService — depends on RAGService interface)
    │   └── models/                       # In-memory conversation repository
    └── frontend/                    # PERSON 3 — Streamlit UI
        ├── pages/ components/ services/ assets/
```

## Why each new piece exists

- **`requirements/`** — see `requirements/README.md`. Person 3 never installs
  FAISS; Person 1 never installs FastAPI. Each role installs exactly what it needs.
- **`rag/interfaces/rag_service_interface.py`** — the *only* contract the
  backend depends on (`RAGService.answer_question`, `.is_ready`). It has zero
  imports from any RAG library, by design.
- **`rag/services/mock_rag_service.py`** — a complete, dependency-free fake
  engine. Not a `NotImplementedError` stub — it returns varied, labeled fake
  answers so the chat UX is genuinely demoable.
- **`rag/services/real_rag_service.py`** — the Indexation & Moteur RAG file. Heavy imports are
  done *lazily inside `__init__`*, so merely having this file in the repo
  never forces anyone to install `person2-rag.txt`.
- **`rag/container.py`** — the single switch. Reads `RAG_MODE` once, builds
  the right service, caches it. Routers never see this decision.
- **`preprocessing/interfaces/data_provider_interface.py`** +
  **`preprocessing/providers/`** — the same Mock/Real/container pattern,
  for Person 1's `DocumentProvider`, `ChunkProvider`, `DatasetLoader`.
- **`analytics/`** — synthetic-but-realistic conversation analytics,
  exportable to CSV for Power BI, so the dashboard requirement is satisfied
  independently of real usage data existing.
- **`core/security.py`** — an authentication placeholder (`get_current_user`)
  already wired into the chat endpoint but not enforced, so real auth later
  is a one-file change instead of a new architecture layer.

## Request flow (unchanged shape, now interface-based end to end)

```
Streamlit (Chat page)
   → frontend/services/api_client.py       (HTTP POST /api/v1/chat)
   → backend/api/routers/chat.py            (validates ChatRequest, injects CurrentUser placeholder)
   → backend/services/chat_service.py        (depends on RAGService interface only)
      → backend/models/conversation.py         (persists messages)
      → rag/container.py → Mock or Real RAGService  (decided by RAG_MODE)
   ← ChatResponse (answer + sources + is_stub flag)
```

## Verified guarantees

- The full app (backend + frontend + tests) runs and passes with
  `RAG_MODE=mock`/`DATA_MODE=mock` and no `faiss`, `langchain`,
  `chromadb`, or `sentence-transformers` installed.
- Setting `RAG_MODE=real` before the Indexation & Moteur RAG implementation
  is finished fails with one clear `NotImplementedError` message, not a
  crash or silent wrong answer.
- The real engine is activated by editing exactly one file
  (`src/rag/services/real_rag_service.py`) and flipping `RAG_MODE=real` —
  zero changes to `backend/` or `frontend/`.
- Person 1 activates real data the same way, in
  `src/preprocessing/providers/real_providers.py` + `DATA_MODE=real`.

## Controlled Darija glossary administration

The French/Darija glossary is seeded into SQLite on first startup. Its
administration API requires an expiring bearer session backed by a
scrypt-hashed administrator password. Every create, update, approval, deletion,
login, and logout is recorded in `admin_audit_log`. Draft and review entries are
never exposed to the RAG lookup; only `approved` terms are loaded.

## Design principles applied

- **Dependency Inversion** — high-level modules (routers, services) depend
  on abstractions (`RAGService`, `DocumentProvider`), never on concrete
  Mock/Real classes.
- **Open/Closed** — adding `RAG_MODE=ollama` later means adding one new
  class + one `if` branch in `container.py`, not touching the backend.
- **Single Responsibility** — each container file has exactly one job:
  decide which implementation to build.
- **DRY / KISS** — one `Settings` object, one `BackendClient`, one theme file,
  one place per DI decision.
