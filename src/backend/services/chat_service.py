"""
Chat service — business logic layer between the API routers and the domain
(RAG pipeline + conversation repository).

Why this layer exists:
    Routers should stay thin (parse request -> call service -> return
    response). Putting logic here instead keeps it testable without spinning
    up FastAPI, and reusable if we ever add another entry point (CLI, batch
    evaluation script for the report's "performance analysis" deliverable).
"""
from src.backend.models.conversation import ConversationRepository
from src.backend.schemas.chat import ChatRequest, ChatResponse, ConversationMessage, SourceCitationSchema
from src.core.exceptions import InvalidRequestError
from src.core.logging_config import get_logger
from src.rag.interfaces.rag_service_interface import RAGService

logger = get_logger(__name__)


class ChatService:
    """Depends only on the `RAGService` interface — it never knows, and never
    remains decoupled from the concrete production RAG implementation."""

    def __init__(self, rag_service: RAGService, conversation_repo: ConversationRepository) -> None:
        self._rag = rag_service
        self._repo = conversation_repo

    def handle_message(self, request: ChatRequest) -> ChatResponse:
        if not request.question.strip():
            raise InvalidRequestError("Question must not be empty.")

        conversation = self._repo.get_or_create(request.conversation_id)

        self._repo.add_message(
            conversation.id,
            ConversationMessage(role="user", content=request.question),
        )

        logger.info("Processing question for conversation %s", conversation.id)
        rag_answer = self._rag.answer_question(request.question, language=request.language)

        sources = [
            SourceCitationSchema(title=s.title, url=s.url, excerpt=s.excerpt) for s in rag_answer.sources
        ]

        self._repo.add_message(
            conversation.id,
            ConversationMessage(role="assistant", content=rag_answer.answer, sources=sources),
        )

        return ChatResponse(
            conversation_id=conversation.id,
            answer=rag_answer.answer,
            sources=sources,
            is_stub=rag_answer.is_mock,
        )
