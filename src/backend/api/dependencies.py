"""
FastAPI dependency-injection providers.

Centralizing `Depends(...)` targets here means routers never construct
services themselves — they declare what they need and FastAPI supplies it.
This is what makes the services trivially unit-testable (swap a fake here in
tests) without touching router code.
"""
from src.backend.models.conversation import ConversationRepository, get_conversation_repository
from src.backend.services.chat_service import ChatService
from src.rag.container import get_rag_service
from src.rag.interfaces.rag_service_interface import RAGService


def get_chat_service() -> ChatService:
    rag_service: RAGService = get_rag_service()
    conversation_repo: ConversationRepository = get_conversation_repository()
    return ChatService(rag_service=rag_service, conversation_repo=conversation_repo)
