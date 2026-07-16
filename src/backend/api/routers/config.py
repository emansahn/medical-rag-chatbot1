"""Public configuration endpoint — non-sensitive settings the frontend needs (never leaks API keys)."""
from fastapi import APIRouter

from src.backend.schemas.common import PublicConfigResponse
from src.core.config import settings

router = APIRouter(tags=["Config"])


@router.get("/config", response_model=PublicConfigResponse, summary="Public frontend configuration")
def get_public_config() -> PublicConfigResponse:
    return PublicConfigResponse(
        app_name=settings.app_name,
        top_k=settings.top_k,
        enable_darija_support=settings.enable_darija_support,
    )
