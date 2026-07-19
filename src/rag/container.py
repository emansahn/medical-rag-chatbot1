"""Production RAG service dependency container."""
from src.core.logging_config import get_logger
from src.rag.interfaces.rag_service_interface import RAGService

logger = get_logger(__name__)

_service_instance: "RAGService | None" = None


def _build_service() -> RAGService:
    logger.info("Instantiating production RealRAGService.")
    from src.rag.services.real_rag_service import RealRAGService

    return RealRAGService()


def get_rag_service() -> RAGService:
    """Singleton accessor, used as a FastAPI dependency."""
    global _service_instance
    if _service_instance is None:
        _service_instance = _build_service()
    return _service_instance
