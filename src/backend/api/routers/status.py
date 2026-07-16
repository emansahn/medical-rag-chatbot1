"""Status endpoint — reports the true readiness of the RAG engine (mock vs real)."""
from fastapi import APIRouter, Depends

from src.backend.schemas.common import StatusResponse
from src.core.config import settings
from src.preprocessing.container import get_chunk_provider
from src.preprocessing.interfaces.data_provider_interface import ChunkProvider
from src.rag.container import get_rag_service
from src.rag.interfaces.rag_service_interface import RAGService

router = APIRouter(tags=["Status"])


@router.get("/status", response_model=StatusResponse, summary="RAG engine integration status")
def get_status(
    rag_service: RAGService = Depends(get_rag_service),
    chunk_provider: ChunkProvider = Depends(get_chunk_provider),
) -> StatusResponse:
    return StatusResponse(
        rag_engine_ready=rag_service.is_ready(),
        rag_mode=settings.rag_mode,
        data_mode=settings.data_mode,
        vector_store_provider=settings.vector_store_provider,
        llm_provider=settings.llm_provider,
        darija_support_enabled=settings.enable_darija_support,
        chunks_indexed=chunk_provider.count(),
    )
