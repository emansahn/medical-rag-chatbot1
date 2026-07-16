"""Shared schemas used across multiple routers."""
from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    app_env: str


class StatusResponse(BaseModel):
    """Surfaces the real integration state of the system, so the frontend can
    show teammates' progress honestly instead of pretending everything is done."""

    rag_engine_ready: bool
    rag_mode: str  # "mock" | "real"
    data_mode: str  # "mock" | "real"
    vector_store_provider: str
    llm_provider: str
    darija_support_enabled: bool
    chunks_indexed: Optional[int] = None


class PublicConfigResponse(BaseModel):
    """Non-sensitive configuration exposed to the frontend (no API keys!)."""

    app_name: str
    top_k: int
    enable_darija_support: bool
    available_languages: list[str] = ["fr", "ary"]


class ErrorResponse(BaseModel):
    error: str
    detail: str
