"""Protected glossary API tests with an isolated temporary SQLite database."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.admin.database import AdminDatabase, get_admin_database
from src.backend.api.routers.admin import router


def _client(tmp_path) -> TestClient:
    database = AdminDatabase(str(tmp_path / "admin-api.db"))
    database.initialize()
    database.create_admin("admin", "a-secure-password")
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_admin_database] = lambda: database
    return TestClient(app)


def test_glossary_requires_authentication(tmp_path):
    response = _client(tmp_path).get("/api/v1/admin/glossary")

    assert response.status_code == 401


def test_admin_can_login_create_and_approve_term(tmp_path):
    client = _client(tmp_path)
    login = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "a-secure-password"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    created = client.post(
        "/api/v1/admin/glossary",
        headers=headers,
        json={
            "french": "palpitations",
            "arabic": "خفقان القلب",
            "latin": "khaf9an l9elb",
            "aliases": ["khaf9an"],
            "status": "draft",
            "notes": "proposition",
        },
    )
    assert created.status_code == 201
    term_id = created.json()["id"]

    approved = client.put(
        f"/api/v1/admin/glossary/{term_id}",
        headers=headers,
        json={"status": "approved", "notes": "validé"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["approved_by"] is not None

    listed = client.get(
        "/api/v1/admin/glossary", headers=headers, params={"status": "approved"}
    )
    assert any(term["id"] == term_id for term in listed.json())


def test_invalid_or_expired_token_is_rejected(tmp_path):
    response = _client(tmp_path).get(
        "/api/v1/admin/auth/me",
        headers={"Authorization": "Bearer invalid"},
    )

    assert response.status_code == 401
