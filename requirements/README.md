# Dependency files — who installs what

| File | Who installs it | Contains |
|---|---|---|
| `base.txt` | everyone (pulled in transitively) | pydantic, settings, dotenv |
| `backend.txt` | Person 3 (API work) | FastAPI, Uvicorn + base |
| `frontend.txt` | Person 3 (UI work) | Streamlit, requests + base |
| `person1-data.txt` | Person 1 only | pypdf, beautifulsoup4, tiktoken |
| `person2-rag.txt` | Person 2 only | sentence-transformers, chromadb, faiss-cpu, langchain |
| `person3-app.txt` | Person 3 (full app) | backend.txt + frontend.txt |
| `dev.txt` | anyone contributing code | pytest, black, ruff |

## Why this matters

Before this split, `pip install -r requirements.txt` forced **everyone** —
including Person 3, who never touches FAISS or LangChain — to install the
heaviest, slowest, most failure-prone libraries in the whole project just to
run the FastAPI server or the Streamlit UI. That's backwards: your work
should never depend on libraries only Person 2's code imports.

## Typical installs

```bash
# Person 3 (this is all you ever need):
pip install -r requirements/person3-app.txt -r requirements/dev.txt

# Person 1:
pip install -r requirements/person1-data.txt -r requirements/dev.txt

# Person 2:
pip install -r requirements/person2-rag.txt -r requirements/backend.txt -r requirements/dev.txt

# CI / "install everything" (rarely needed):
pip install -r requirements/person3-app.txt -r requirements/person1-data.txt -r requirements/person2-rag.txt -r requirements/dev.txt
```

The root-level `requirements.txt` is kept only as a convenience alias for
"install everything" (useful for CI or a full demo box) — see its header comment.
