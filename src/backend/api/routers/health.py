"""Liveness/health check — used by load balancers, Docker healthchecks, and the frontend."""
from fastapi import APIRouter

from src.backend.schemas.common import HealthResponse
from src.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", app_name=settings.app_name, app_env=settings.app_env)
