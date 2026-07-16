"""Chat endpoints — the core of the application."""
from fastapi import APIRouter, Depends

from src.backend.api.dependencies import get_chat_service
from src.backend.schemas.chat import ChatRequest, ChatResponse
from src.backend.services.chat_service import ChatService
from src.core.security import CurrentUser, get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, summary="Ask the medical chatbot a question")
def post_chat_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> ChatResponse:
    """Send a question and get a RAG-grounded answer with source citations.

    While `RAG_MODE=mock`, `is_stub=true` is returned so the frontend can
    display an honest "demo mode" badge. `current_user` is a placeholder
    (see `src/core/security.py`) — not enforced today, but already wired so
    real authentication is a one-file change later.
    """
    return chat_service.handle_message(request)
