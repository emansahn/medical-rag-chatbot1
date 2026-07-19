"""SQLite authentication and glossary workflow tests."""

from src.admin.database import AdminDatabase, hash_password, verify_password


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("a-secure-password")
    second = hash_password("a-secure-password")

    assert first != second
    assert verify_password("a-secure-password", first)
    assert not verify_password("wrong-password", first)


def test_admin_session_and_approved_glossary_workflow(tmp_path):
    database = AdminDatabase(str(tmp_path / "admin.db"))
    database.initialize()
    admin = database.create_admin("reviewer", "a-secure-password")

    authenticated = database.authenticate("reviewer", "a-secure-password")
    assert authenticated is not None
    token, identity = authenticated
    assert identity["id"] == admin["id"]
    assert database.admin_for_token(token)["username"] == "reviewer"

    term = database.create_term(
        {
            "french": "palpitations",
            "arabic": "خفقان القلب",
            "latin": "khaf9an l9elb",
            "aliases": ["khaf9an"],
            "status": "draft",
            "notes": "À valider",
        },
        admin["id"],
    )
    assert not any(row["id"] == term["id"] for row in database.approved_terms())

    approved = database.update_term(
        term["id"], {"status": "approved"}, admin["id"]
    )
    assert approved["approved_by"] == admin["id"]
    assert any(row["id"] == term["id"] for row in database.approved_terms())

    database.logout(token, admin["id"])
    assert database.admin_for_token(token) is None
    assert database.audit_log()
