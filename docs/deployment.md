# Deployment Guide

## Option A — Local (development, already covered in installation.md)

## Option B — Docker Compose

`Dockerfile.backend` (installs backend deps + whichever of person1/person2's
files match your `.env` mode — mock mode needs neither):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/backend.txt
# For RAG_MODE=real, also: RUN pip install --no-cache-dir -r requirements/person2-rag.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`Dockerfile.frontend`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/frontend.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "src/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

`docker-compose.yml`:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./data:/app/data

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8501:8501"
    env_file: .env
    environment:
      - BACKEND_API_URL=http://backend:8000/api/v1
    depends_on:
      - backend
```

```bash
docker compose up --build
```

## Option C — Cloud demo (for the defense)

- **Backend:** any container host (Render, Railway, Fly.io) exposing port 8000.
- **Frontend:** Streamlit Community Cloud, pointing `BACKEND_API_URL` at the
  deployed backend URL via that platform's secrets/env config.
- Keep `LLM_API_KEY` out of git; set it as a platform secret.

## Production hardening checklist (beyond academic scope, good to mention in the report)

- Swap the in-memory `ConversationRepository` for PostgreSQL.
- Add rate limiting on `/chat`.
- Add request/response logging with correlation IDs.
- Add authentication (the architecture already reserves a slot for this —
  see `docs/future_improvements.md`).
