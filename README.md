# 🩺 Medical Intelligent Chatbot — RAG adapted to the Moroccan context

Master's project — Université Chouaïb Doukkali, Faculté des Sciences, El Jadida
Module: *Programmation Python Avancée* — AU 2025/2026

A Retrieval-Augmented Generation (RAG) chatbot that answers medical questions
using **only trusted Moroccan medical sources**, with optional Darija ↔
Français support. The application runs exclusively against the production
PDF corpus and vector index; fake runtime modes are intentionally disabled.

The active corpus is configured with `CHUNKS_PATH`; the persistent Chroma
index is configured with `VECTOR_STORE_PATH`.

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
| `rag_engine_ready` | `True` only once the Indexation & Moteur RAG engine reports ready |
| `chunks_indexed` | Count from the production clinical corpus |

## 4. Documentation

- [`docs/architecture.md`](docs/architecture.md) — architecture and folder rationale
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
