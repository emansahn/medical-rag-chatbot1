"""Integration tests hitting the FastAPI app through TestClient (no live server needed)."""
from fastapi.testclient import TestClient

from src.backend.main import app

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


def test_chat_endpoint_returns_stub_answer():
    response = client.post("/api/v1/chat", json={"question": "Quels sont les signes du diabète ?"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_stub"] is True
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


def test_status_endpoint_reports_mock_mode_by_default():
    response = client.get("/api/v1/status")
    body = response.json()
    assert body["rag_mode"] == "mock"
    assert body["data_mode"] == "mock"
    assert body["chunks_indexed"] is not None and body["chunks_indexed"] > 0


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
