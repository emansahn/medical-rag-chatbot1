"""Integration tests hitting the FastAPI app through TestClient (no live server needed)."""
from fastapi.testclient import TestClient

from src.backend.api.dependencies import get_chat_service
from src.backend.main import app
from src.backend.models.conversation import ConversationRepository
from src.backend.services.chat_service import ChatService
from src.preprocessing.container import get_chunk_provider
from src.rag.container import get_rag_service
from src.rag.interfaces.rag_service_interface import RAGAnswer, RAGService, SourceCitation


class _TestRAGService(RAGService):
    def is_ready(self) -> bool:
        return True

    def answer_question(self, question: str, language: str = "fr") -> RAGAnswer:
        return RAGAnswer(
            answer=f"Réponse de test fondée: {question}",
            sources=[SourceCitation("Guide", "https://example.ma/guide", "Extrait")],
        )


class _TestChunkProvider:
    def count(self) -> int:
        return 37


_test_rag = _TestRAGService()
app.dependency_overrides[get_rag_service] = lambda: _test_rag
app.dependency_overrides[get_chunk_provider] = lambda: _TestChunkProvider()
app.dependency_overrides[get_chat_service] = lambda: ChatService(
    _test_rag, ConversationRepository()
)

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_endpoint():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    body = response.json()
    assert "rag_engine_ready" in body


def test_config_endpoint_hides_secrets():
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    body = response.json()
    assert "llm_api_key" not in body


def test_chat_endpoint_returns_real_answer_contract():
    response = client.post("/api/v1/chat", json={"question": "Quels sont les signes du diabète ?"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_stub"] is False
    assert body["conversation_id"]
    assert len(body["answer"]) > 0


def test_chat_endpoint_rejects_empty_question():
    response = client.post("/api/v1/chat", json={"question": "   "})
    assert response.status_code == 422  # Pydantic validation error


def test_chat_endpoint_rejects_unknown_language():
    response = client.post(
        "/api/v1/chat",
        json={"question": "Question", "language": "unknown"},
    )

    assert response.status_code == 422


def test_status_endpoint_reports_production_corpus():
    response = client.get("/api/v1/status")
    body = response.json()
    assert "rag_mode" not in body
    assert "data_mode" not in body
    assert body["chunks_indexed"] == 37


def test_analytics_summary_endpoint():
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_conversations"] > 0
    assert body["is_sample_data"] is True


def test_analytics_export_endpoint():
    response = client.post("/api/v1/analytics/export")
    assert response.status_code == 200
    body = response.json()
    assert body["record_count"] > 0
    assert body["file_path"].endswith(".csv")
