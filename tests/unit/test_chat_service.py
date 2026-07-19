"""Unit tests for the chat service using an isolated RAG test double."""
import pytest

from src.backend.models.conversation import ConversationRepository
from src.backend.schemas.chat import ChatRequest
from src.backend.services.chat_service import ChatService
from src.rag.interfaces.rag_service_interface import RAGAnswer, RAGService


class _FakeRAGService(RAGService):
    def is_ready(self) -> bool:
        return True

    def answer_question(self, question: str, language: str = "fr") -> RAGAnswer:
        return RAGAnswer(answer=f"Réponse réelle simulée pour le test: {question}", is_mock=False)


@pytest.fixture
def chat_service() -> ChatService:
    return ChatService(rag_service=_FakeRAGService(), conversation_repo=ConversationRepository())


def test_handle_message_creates_conversation(chat_service: ChatService):
    request = ChatRequest(question="Quels sont les symptômes du diabète ?")
    response = chat_service.handle_message(request)

    assert response.conversation_id
    assert response.answer
    assert response.is_stub is False


def test_handle_message_reuses_conversation_id(chat_service: ChatService):
    first = chat_service.handle_message(ChatRequest(question="Qu'est-ce que l'hypertension ?"))
    second = chat_service.handle_message(
        ChatRequest(question="Et comment la prévenir ?", conversation_id=first.conversation_id)
    )
    assert first.conversation_id == second.conversation_id


def test_handle_message_rejects_blank_question(chat_service: ChatService):
    with pytest.raises(Exception):
        # Pydantic itself rejects this at schema level (min_length=1 + validator),
        # but we also guard in the service layer for defense in depth.
        ChatRequest(question="   ")
