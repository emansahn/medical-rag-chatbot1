# Collaboration Workflow

## Folder responsibility — who touches what

| Folder | Owner | Others should... |
|---|---|---|
| `src/preprocessing/providers/`, `src/preprocessing/loaders/` `cleaning/` `chunking/` (to create) | **Person 1** | never import from directly — depend on `DocumentProvider`/`ChunkProvider` interfaces |
| `src/rag/services/`, `src/rag/embedders/` `vector_stores/` `retrievers/` `prompting/` `llm/` (to create) | **Indexation & Moteur RAG** | never import from directly — depend on `RAGService` interface |
| `src/backend/`, `src/frontend/`, `src/analytics/`, `src/core/` | **Person 3** | Person 1 and Indexation & Moteur RAG should not need to touch these at all |
| `src/preprocessing/interfaces/`, `src/rag/interfaces/`, `*/container.py` | **Shared contract** — changes here need agreement from whoever depends on them | propose changes via PR, tag the affected owner as reviewer |
| `docs/`, `requirements/` | **Person 3** maintains, anyone can propose edits | |

## Branch strategy

```
main                    ← always demoable, protected, mock mode passes CI
├── feature/person1-<topic>   e.g. feature/person1-pdf-loader
├── feature/person2-<topic>   e.g. feature/person2-chroma-store
└── feature/person3-<topic>   e.g. feature/person3-analytics-dashboard
```

- Never commit directly to `main`.
- Branch names are prefixed by owner so `git log --graph` and PR lists stay
  scannable for a 3-person team.
- Keep branches short-lived (a few days). Because everyone works behind an
  interface, there is rarely a reason for a branch to live longer than the
  feature it implements.

## Pull request workflow

1. Open a PR from your `feature/personN-*` branch into `main`.
2. PR description states: what interface(s) you implemented, and confirms
   `RAG_MODE=mock`/`DATA_MODE=mock` still boot correctly if you touched
   anything outside your own folder.
3. Run `pytest tests/ -v` locally before requesting review — see Testing below.
4. At least one other teammate approves. For changes to a **shared
   interface** (`*/interfaces/*.py`, `*/container.py`), all three must
   approve, since it changes everyone's contract.
5. Squash-merge to keep `main` history readable.

## Integration process

### Person 1 → Indexation & Moteur RAG / Person 3
1. Implement `DocumentLoader`/`TextCleaner`/`TextChunker`
   (`src/preprocessing/interfaces/document_loader_interface.py`).
2. Write `src/preprocessing/pipeline.py` to run them and populate `data/chunks/`.
3. Implement `RealDocumentProvider`/`RealChunkProvider`/`RealDatasetLoader`
   in `src/preprocessing/providers/real_providers.py` (a starting version
   already exists — just confirm the file format matches your chunker's output).
4. Set `DATA_MODE=real` in `.env` locally to verify, then open a PR.
5. **Nothing in `src/backend/` or `src/frontend/` should be touched.**

### Indexation & Moteur RAG → Person 3
1. Implement `Embedder`, `VectorStore`/`Retriever`, `PromptBuilder`, `LLMClient`
   (`src/rag/interfaces/`).
2. Write `src/rag/ingest.py` to embed Person 1's chunks into your vector store.
3. Fill in `src/rag/services/real_rag_service.py` (`__init__` + `answer_question`
   + `is_ready`) using those components — a commented template is already in the file.
4. Set `RAG_MODE=real` in `.env` locally to verify, then open a PR.
5. **Nothing in `src/backend/` or `src/frontend/` should be touched.**

### Merge order recommendation
Person 1 and Indexation & Moteur RAG can merge in **any order**,
independently, since the RAG ingestion script reads from `data/chunks/`
regardless of when Person 1's PR lands. Person 3's work never blocks on
either.

## Testing process

```bash
pip install -r requirements/dev.txt -r requirements/person3-app.txt
pytest tests/ -v
```

- **Unit tests** (`tests/unit/`) — no server, no network. Person 1 and
  Indexation & Moteur RAG add tests here for their own
  loaders/embedders/retrievers as they build them (e.g.
  `tests/unit/preprocessing/`, `tests/unit/rag/`).
- **Integration tests** (`tests/integration/`) — hit the FastAPI app via
  `TestClient`, always run against whatever `RAG_MODE`/`DATA_MODE` is
  active. CI runs these in `mock` mode (fast, no external services).
- Before merging a `real_rag_service.py` or `real_providers.py` change,
  additionally run with `RAG_MODE=real`/`DATA_MODE=real` locally at least
  once to confirm your implementation actually satisfies the interface
  (the abstract base classes will raise `TypeError` at instantiation if a
  method is missing — that's an intentional early failure).

## Golden rule

> If your change requires editing a file outside your own folder (other
> than `*/interfaces/*.py` or `*/container.py`, with review), stop and ask
> whether the interface is missing something — that's the actual bug to fix.
