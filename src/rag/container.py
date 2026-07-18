"""
RAG service container — the single place that decides which `RAGService`
implementation the app runs against.

Controlled by `RAG_MODE` in `.env`:
    RAG_MODE=mock   (default) -> MockRAGService, zero heavy dependencies.
    RAG_MODE=real              -> RealRAGService, requires
                                   requirements/person2-rag.txt and a
                                   finished Indexation & Moteur RAG implementation.

Nothing outside this file ever chooses between Mock/Real directly — routers
and services only ever see the `RAGService` interface (dependency inversion).
"""
from src.core.config import settings
from src.core.logging_config import get_logger
from src.rag.interfaces.rag_service_interface import RAGService

logger = get_logger(__name__)

_service_instance: "RAGService | None" = None


def _build_service() -> RAGService:
    if settings.rag_mode == "real":
        logger.info("RAG_MODE=real — instantiating RealRAGService (Indexation & Moteur RAG engine).")
        from src.rag.services.real_rag_service import RealRAGService  # local import: only pulled in when needed

        return RealRAGService()

    logger.info("RAG_MODE=mock — instantiating MockRAGService (no RAG dependencies required).")
    from src.rag.services.mock_rag_service import MockRAGService

    return MockRAGService()


def get_rag_service() -> RAGService:
    """Singleton accessor, used as a FastAPI dependency."""
    global _service_instance
    if _service_instance is None:
        _service_instance = _build_service()
    return _service_instance
