# 🩺 Medical Intelligent Chatbot — RAG adapted to the Moroccan context

Master's project — Université Chouaïb Doukkali, Faculté des Sciences, El Jadida
Module: *Programmation Python Avancée* — AU 2025/2026

A Retrieval-Augmented Generation (RAG) chatbot that answers medical questions
using **only trusted Moroccan medical sources**, with optional Darija ↔
Français support — architected so **three people can build it fully in
parallel**, and so the application **always runs**, even before any of the
RAG or data-collection work is finished.

---
```
RAG_MODE=mock|real      # default: mock — MockRAGService, zero RAG libraries required
DATA_MODE=mock|real     # default: mock — sample documents/chunks, zero scraping libraries required
```

**The application boots and is fully demoable in mock mode today**, with
realistic fake answers and sources, before the data-collection or
Indexation & Moteur RAG work is finished. See `docs/architecture.md` for the
full rationale.

## 2. Quick start (Person 3 / anyone demoing)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements/person3-app.txt -r requirements/dev.txt
cp .env.example .env

# Terminal 1 — API
uvicorn src.backend.main:app --reload --port 8000

# Terminal 2 — UI
streamlit run src/frontend/app.py
```

Open http://localhost:8501 for the chat UI, http://localhost:8000/docs for
the API reference. Or run both with `bash scripts/run_dev.sh`.

## 3. Integration status (surfaced live at `/api/v1/status`)

| Flag | Meaning |
|---|---|
| `rag_mode` | `mock` (default) or `real` |
| `data_mode` | `mock` (default) or `real` |
| `rag_engine_ready` | `True` only once the Indexation & Moteur RAG engine reports ready |
| `chunks_indexed` | Count from whichever `ChunkProvider` is active |

## 4. Documentation

- [`docs/architecture.md`](docs/architecture.md) — the Mock/Real/Container
  pattern, folder-by-folder rationale, verified independence guarantees
- [`docs/collaboration_workflow.md`](docs/collaboration_workflow.md) — git
  branching, PR review rules, integration & testing process
- [`docs/installation.md`](docs/installation.md) — setup guide
- [`docs/developer_guide.md`](docs/developer_guide.md) — coding standards,
  how each person integrates their work
- [`docs/deployment.md`](docs/deployment.md) — Docker / deployment guide
- [`docs/future_improvements.md`](docs/future_improvements.md) — roadmap
- [`requirements/README.md`](requirements/README.md) — who installs what, and why

## 5. Analytics dashboard / Power BI

`GET /api/v1/analytics/summary` and `POST /api/v1/analytics/export` generate
realistic synthetic usage data into `data/analytics/conversations.csv` —
Power BI connects to that folder/file today (**Get Data → Folder** or
**Text/CSV**), independently of real conversation history existing yet.

## 6. License / academic notice

Built for academic purposes. Not a certified medical device — always direct
users to a real healthcare professional for diagnosis or emergencies.
