"""
Centralized application configuration.

Every setting the app needs — backend, frontend, and RAG engine — is declared
here as a single source of truth, loaded from environment variables / `.env`.

Why this exists:
    Hardcoded values scattered across files are a maintenance trap and a
    security risk (secrets in code). `pydantic-settings` gives us validation,
    type safety, and one predictable place to look when something is
    misconfigured.

Who owns this:
    Person 3 (infra/config). Person 1 and the Indexation & Moteur RAG module should ADD new fields here
    (e.g. `CHUNK_SIZE`, `LLM_TEMPERATURE`) rather than hardcoding constants in
    their own modules, so every teammate can see the full configuration surface.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings, populated from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    app_name: str = "Medical RAG Chatbot"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # --- Backend API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:8501"

    # --- Frontend ---
    backend_api_url: str = "http://localhost:8000/api/v1"

    # --- Mode switches (dependency injection control) ---
    # "mock" requires no heavy libraries; "real" requires the data-collection
    # and Indexation & Moteur RAG implementations + their requirements files to be installed.
    rag_mode: str = "mock"       # mock | real
    data_mode: str = "mock"      # mock | real

    # --- RAG engine (Indexation & Moteur RAG) ---
    llm_provider: str = "ollama"     # ollama (local, default) | openai
    llm_model_name: str = "llama3.1:8b"
    llm_api_key: str = ""
    llm_base_url: str = "http://localhost:11434"
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    vector_store_provider: str = "chroma"
    vector_store_path: str = "./data/vector_store"
    top_k: int = 4

    # --- Multilingual bonus ---
    enable_darija_support: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so the .env file is parsed only once."""
    return Settings()


settings = get_settings()
