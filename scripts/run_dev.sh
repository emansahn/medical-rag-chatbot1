#!/usr/bin/env bash
# Runs the FastAPI backend and Streamlit frontend together for local dev.
# Usage: bash scripts/run_dev.sh
set -e

cd "$(dirname "$0")/.."

echo "Starting backend on :8000 ..."
uvicorn src.backend.main:app --reload --port 8000 &
BACKEND_PID=$!

trap "echo 'Stopping backend...'; kill $BACKEND_PID" EXIT

sleep 2
echo "Starting frontend on :8501 ..."
streamlit run src/frontend/app.py
