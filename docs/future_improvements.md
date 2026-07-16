# Future Improvements

Ideas inspired by real-world AI products (ChatGPT, Claude, Perplexity),
beyond what's required for the module deliverable — useful for the report's
"perspectives" section and for scoring extra points.

## Near-term (natural next steps)
- Persist conversations in PostgreSQL instead of in-memory (repository
  interface already isolates this change to one file).
- Streaming responses (token-by-token) instead of a single blocking call,
  using FastAPI `StreamingResponse` + Streamlit's `st.write_stream`.
- Real Darija ↔ Français translation layer (currently a config flag +
  documented approach, not implemented) using a small MT model or LLM call.
- Answer confidence indicator: surface the retrieval similarity scores
  (`RetrievedChunk.score`) in the UI so users see how grounded an answer is.

## Medium-term
- User accounts + auth (JWT), so conversation history persists per user
  across sessions/devices — the backend already has a clean seam for this
  in `src/backend/api/dependencies.py`.
- Feedback loop: thumbs up/down on answers, stored and used to flag weak
  retrieval or prompt issues (useful for the "performance analysis" report).
- Automated evaluation harness: a small labeled Q&A set + a script scoring
  retrieval precision/recall and answer faithfulness (RAGAS-style metrics).
- Admin dashboard for Person 1/2 to monitor ingestion status, chunk counts,
  and re-index on demand — building on the existing `/status` endpoint.

## Long-term / stretch
- Multi-turn context-aware retrieval (rewrite follow-up questions using
  conversation history before embedding).
- Source-highlighting: show exactly which sentence of a source document
  supported a given claim.
- Voice input/output for accessibility in low-literacy contexts.
- Fine-tuned or distilled small model for on-device / offline use in areas
  with poor connectivity — directly addresses the brief's stated problem of
  limited access to care in some regions.
