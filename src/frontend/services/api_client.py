"""
Backend API communication layer.

Why this exists:
    Keeps every `requests` call and error-handling decision in one place, so
    Streamlit pages/components never talk HTTP directly. If the API contract
    changes, only this file changes.
"""
from dataclasses import dataclass
from typing import List, Optional

import requests

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

_TIMEOUT_SECONDS = 30
_CHAT_TIMEOUT_SECONDS = 120  # local LLM generation (e.g. Ollama on CPU) can take well over 30s


@dataclass
class ApiError(Exception):
    message: str
    status_code: Optional[int] = None


class BackendClient:
    """Thin, typed wrapper around the FastAPI backend."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.backend_api_url).rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health(self) -> dict:
        return self._get("/health")

    def status(self) -> dict:
        return self._get("/status")

    def public_config(self) -> dict:
        return self._get("/config")

    def send_message(self, question: str, conversation_id: Optional[str], language: str = "fr") -> dict:
        payload = {"question": question, "conversation_id": conversation_id, "language": language}
        return self._post("/chat", payload, timeout=_CHAT_TIMEOUT_SECONDS)

    def _get(self, path: str) -> dict:
        try:
            response = requests.get(self._url(path), timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error("GET %s failed: %s", path, exc)
            raise ApiError(message=f"Could not reach the backend ({path}). Is it running?") from exc

    def _post(self, path: str, payload: dict, timeout: int = _TIMEOUT_SECONDS) -> dict:
        try:
            response = requests.post(self._url(path), json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            detail = ""
            try:
                detail = exc.response.json().get("detail", "")
            except Exception:
                pass
            logger.error("POST %s failed: %s | %s", path, exc, detail)
            raise ApiError(message=detail or str(exc), status_code=exc.response.status_code) from exc
        except requests.exceptions.RequestException as exc:
            logger.error("POST %s failed: %s", path, exc)
            raise ApiError(message="Could not reach the backend. Is it running on the configured URL?") from exc


_client_instance: "BackendClient | None" = None


def get_backend_client() -> BackendClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = BackendClient()
    return _client_instance
