# Installation Guide

## Prerequisites

- Python 3.11+ (developed/tested on 3.12)
- pip

## Steps

```bash
git clone <repo-url>
cd medical-rag-chatbot

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements/person3-app.txt -r requirements/dev.txt

cp .env.example .env             # adjust values if needed
```

Only need the full app? That's it — `RAG_MODE` and `DATA_MODE` default to
`mock`, so nothing from `requirements/person1-data.txt` or
`requirements/person2-rag.txt` is required. See `requirements/README.md`
for what each role installs.

## Running the app

Two processes, two terminals, from the project root (so Python can resolve
`from src...` imports):

```bash
# Terminal 1 — backend API
uvicorn src.backend.main:app --reload --port 8000

# Terminal 2 — frontend UI
streamlit run src/frontend/app.py
```

Or use the convenience script:

```bash
bash scripts/run_dev.sh
```

- API docs (Swagger): http://localhost:8000/docs
- Chat UI: http://localhost:8501

## Running tests

```bash
pytest tests/ -v
```

## Common issues

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'src'` when running `streamlit run` | Already handled: every entry point (`app.py`, `pages/*.py`) adds the project root to `sys.path` itself at the top of the file, so no `PYTHONPATH` is needed. If you still hit this, the project folder was likely renamed/moved in a way that changed its depth (e.g. extracted twice into a nested `(1)` folder on Windows) — run from the actual `medical-rag-chatbot` folder that directly contains `src/`, `requirements/`, etc. |
| `ModuleNotFoundError: No module named 'src'` when running the backend | Run `uvicorn` from the project root, not from inside `src/` |
| Frontend shows "Backend hors-ligne" | Make sure `uvicorn` is running on the port set by `API_PORT` in `.env` |
| `pip install` fails on `faiss-cpu` | Not required to run the demo (mock mode); only needed once Person 2 wires FAISS in via `requirements/person2-rag.txt` |
