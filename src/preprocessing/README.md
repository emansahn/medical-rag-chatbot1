# `src/preprocessing/` — Person 1's workspace

**Goal:** turn raw Moroccan medical sources (PDFs, official web pages) into a
clean list of `DocumentChunk` objects that the Indexation & Moteur RAG
engine (`src/rag/`) can embed and index.

**Install only:** `pip install -r requirements/person1-data.txt -r requirements/dev.txt`
— you never need FastAPI, Streamlit, or any RAG library to do your job.

## What already exists (do not need to touch)

- `interfaces/document_loader_interface.py` — internal contracts:
  `RawDocument`, `DocumentLoader`, `TextCleaner`, `TextChunker`, `DocumentChunk`.
- `interfaces/data_provider_interface.py` — the **app-facing** contract:
  `DocumentProvider`, `ChunkProvider`, `DatasetLoader`, `Dataset`. This is
  what the rest of the app (analytics, dashboard, future admin tools) depends on.
- `providers/mock_providers.py` — already-working sample data. This is why
  the whole app runs today without you having collected anything yet.
- `providers/real_providers.py` — your integration point (see below).
- `container.py` — reads `DATA_MODE` from `.env` and returns Mock or Real.
  You never edit this file.

## What you build here

```
src/preprocessing/
├── loaders/
│   ├── pdf_loader.py        # class MinsanteDocPDFLoader(DocumentLoader): ...
│   └── web_loader.py        # class OMSMarocWebLoader(DocumentLoader): ...
├── cleaning/
│   └── french_medical_cleaner.py   # class FrenchMedicalCleaner(TextCleaner): ...
├── chunking/
│   └── token_chunker.py     # class TokenOverlapChunker(TextChunker): ...
└── pipeline.py               # orchestrates loaders -> cleaner -> chunker
                               # -> writes data/processed/*.json and data/chunks/*.jsonl
```

## Contract you must respect

1. `DocumentLoader.load()` returns `list[RawDocument]` — extraction only, no cleaning.
2. `TextCleaner.clean()` is a pure function: raw text in, cleaned text out.
3. `TextChunker.chunk()` returns `list[DocumentChunk]`, **300–800 tokens with
   overlap** (per project spec).
4. Persist: `RawDocument`s as JSON to `data/processed/`, `DocumentChunk`s as
   JSONL to `data/chunks/` — `providers/real_providers.py` already reads
   from exactly these paths. If your field names differ, adjust that file
   (it's the one file you're expected to touch, since it's your integration seam).

## Activating your real data

```bash
# .env
DATA_MODE=real
```
Restart the backend. `/api/v1/status` and the sidebar will now report real
chunk counts instead of the mock sample count.

## Testing

`tests/unit/preprocessing/` (create this folder). At minimum: cleaner
strips boilerplate reliably; chunker respects 300–800 tokens/overlap;
`source_url`/`source_title` survive the full pipeline (needed for citations).

## You do NOT need to touch

`src/backend/`, `src/frontend/`, `src/rag/`, `src/analytics/`.
