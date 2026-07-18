"""
Application-wide logging setup.

Why this exists:
    A RAG pipeline has many failure points (empty retrieval, LLM timeout,
    malformed documents...). Consistent, structured logs are what makes
    those failures debuggable instead of mysterious. Every module should
    call `get_logger(__name__)` instead of using `print()`.

Who owns this:
    Person 3. Person 1 and the Indexation & Moteur RAG module simply import
    `get_logger` in their modules — no need to touch this file.
"""
import logging
import sys

from src.core.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging() -> None:
    """Configure the root logger once, at application startup."""
    global _configured
    if _configured:
        return

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        stream=sys.stdout,
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Ensures logging is configured before first use."""
    configure_logging()
    return logging.getLogger(name)
