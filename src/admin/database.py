"""SQLite persistence for administrators, glossary workflow, and audit logs."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
from typing import Iterator

from src.core.config import settings
from src.rag.translation.medical_glossary import MEDICAL_GLOSSARY


GLOSSARY_STATUSES = {"draft", "linguistic_review", "medical_review", "approved", "rejected"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Administrator passwords must contain at least 12 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = encoded.split("$", 2)
        if algorithm != "scrypt":
            return False
        candidate = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1
        )
        return hmac.compare_digest(candidate, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


class AdminDatabase:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or settings.admin_db_path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS glossary_terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    french TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    arabic TEXT NOT NULL,
                    latin TEXT NOT NULL,
                    aliases_json TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'draft',
                    notes TEXT NOT NULL DEFAULT '',
                    created_by INTEGER REFERENCES admins(id),
                    updated_by INTEGER REFERENCES admins(id),
                    approved_by INTEGER REFERENCES admins(id),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    approved_at TEXT
                );
                CREATE TABLE IF NOT EXISTS admin_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER REFERENCES admins(id),
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_glossary_status ON glossary_terms(status);
                CREATE INDEX IF NOT EXISTS idx_sessions_hash ON admin_sessions(token_hash);
                """
            )
            self._seed_glossary(db)
        self.bootstrap_admin()

    def _seed_glossary(self, db: sqlite3.Connection) -> None:
        now = _iso(_utc_now())
        for french, entry in MEDICAL_GLOSSARY.items():
            db.execute(
                """INSERT OR IGNORE INTO glossary_terms
                   (french, arabic, latin, aliases_json, status, notes, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'approved', ?, ?, ?)""",
                (
                    french,
                    entry.arabic,
                    entry.latin,
                    json.dumps(entry.aliases, ensure_ascii=False),
                    "Glossaire initial livré avec le projet; validation humaine recommandée.",
                    now,
                    now,
                ),
            )

    def bootstrap_admin(self) -> bool:
        username = settings.admin_bootstrap_username.strip()
        password = settings.admin_bootstrap_password
        if not username or not password:
            return False
        with self.connect() as db:
            exists = db.execute("SELECT 1 FROM admins LIMIT 1").fetchone()
            if exists:
                return False
            cursor = db.execute(
                "INSERT INTO admins(username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hash_password(password), _iso(_utc_now())),
            )
            self._audit(db, cursor.lastrowid, "bootstrap", "admin", cursor.lastrowid, {})
        return True

    def create_admin(self, username: str, password: str) -> dict:
        username = username.strip()
        if not username:
            raise ValueError("Administrator username cannot be empty.")
        with self.connect() as db:
            cursor = db.execute(
                "INSERT INTO admins(username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hash_password(password), _iso(_utc_now())),
            )
            admin_id = cursor.lastrowid
            self._audit(db, admin_id, "create", "admin", admin_id, {})
            return {"id": admin_id, "username": username}

    def authenticate(self, username: str, password: str) -> tuple[str, dict] | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM admins WHERE username = ? COLLATE NOCASE AND is_active = 1",
                (username.strip(),),
            ).fetchone()
            if not row or not verify_password(password, row["password_hash"]):
                return None
            token = secrets.token_urlsafe(32)
            expires_at = _utc_now() + timedelta(hours=settings.admin_session_hours)
            db.execute(
                "INSERT INTO admin_sessions(admin_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (row["id"], self._token_hash(token), _iso(expires_at), _iso(_utc_now())),
            )
            self._audit(db, row["id"], "login", "admin", row["id"], {})
            return token, {"id": row["id"], "username": row["username"], "expires_at": _iso(expires_at)}

    def admin_for_token(self, token: str) -> dict | None:
        with self.connect() as db:
            row = db.execute(
                """SELECT a.id, a.username, s.expires_at FROM admin_sessions s
                   JOIN admins a ON a.id = s.admin_id
                   WHERE s.token_hash = ? AND a.is_active = 1 AND s.expires_at > ?""",
                (self._token_hash(token), _iso(_utc_now())),
            ).fetchone()
            return dict(row) if row else None

    def logout(self, token: str, admin_id: int) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM admin_sessions WHERE token_hash = ?", (self._token_hash(token),))
            self._audit(db, admin_id, "logout", "admin", admin_id, {})

    def list_terms(self, status: str | None = None, search: str = "") -> list[dict]:
        sql = "SELECT * FROM glossary_terms WHERE 1=1"
        values: list[object] = []
        if status:
            sql += " AND status = ?"
            values.append(status)
        if search.strip():
            sql += " AND (french LIKE ? OR arabic LIKE ? OR latin LIKE ?)"
            needle = f"%{search.strip()}%"
            values.extend([needle, needle, needle])
        sql += " ORDER BY french COLLATE NOCASE"
        with self.connect() as db:
            return [self._term_dict(row) for row in db.execute(sql, values).fetchall()]

    def approved_terms(self) -> list[dict]:
        return self.list_terms(status="approved")

    def create_term(self, payload: dict, admin_id: int) -> dict:
        now = _iso(_utc_now())
        with self.connect() as db:
            cursor = db.execute(
                """INSERT INTO glossary_terms
                   (french, arabic, latin, aliases_json, status, notes, created_by,
                    updated_by, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    payload["french"].strip(), payload["arabic"].strip(),
                    payload["latin"].strip(), json.dumps(payload.get("aliases", []), ensure_ascii=False),
                    payload.get("status", "draft"), payload.get("notes", "").strip(),
                    admin_id, admin_id, now, now,
                ),
            )
            term_id = cursor.lastrowid
            self._audit(db, admin_id, "create", "glossary_term", term_id, payload)
            row = db.execute("SELECT * FROM glossary_terms WHERE id = ?", (term_id,)).fetchone()
            return self._term_dict(row)

    def update_term(self, term_id: int, payload: dict, admin_id: int) -> dict | None:
        with self.connect() as db:
            current = db.execute("SELECT * FROM glossary_terms WHERE id = ?", (term_id,)).fetchone()
            if not current:
                return None
            values = self._term_dict(current)
            values.update({key: value for key, value in payload.items() if value is not None})
            status = values["status"]
            approved_by = admin_id if status == "approved" else None
            approved_at = _iso(_utc_now()) if status == "approved" else None
            db.execute(
                """UPDATE glossary_terms SET french=?, arabic=?, latin=?, aliases_json=?,
                   status=?, notes=?, updated_by=?, updated_at=?, approved_by=?, approved_at=?
                   WHERE id=?""",
                (
                    values["french"].strip(), values["arabic"].strip(), values["latin"].strip(),
                    json.dumps(values.get("aliases", []), ensure_ascii=False), status,
                    values.get("notes", "").strip(), admin_id, _iso(_utc_now()), approved_by,
                    approved_at, term_id,
                ),
            )
            self._audit(db, admin_id, "update", "glossary_term", term_id, payload)
            row = db.execute("SELECT * FROM glossary_terms WHERE id = ?", (term_id,)).fetchone()
            return self._term_dict(row)

    def delete_term(self, term_id: int, admin_id: int) -> bool:
        with self.connect() as db:
            exists = db.execute("SELECT french FROM glossary_terms WHERE id = ?", (term_id,)).fetchone()
            if not exists:
                return False
            db.execute("DELETE FROM glossary_terms WHERE id = ?", (term_id,))
            self._audit(db, admin_id, "delete", "glossary_term", term_id, {"french": exists["french"]})
            return True

    def audit_log(self, limit: int = 100) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                """SELECT l.*, a.username FROM admin_audit_log l
                   LEFT JOIN admins a ON a.id = l.admin_id
                   ORDER BY l.id DESC LIMIT ?""",
                (min(max(limit, 1), 500),),
            ).fetchall()
            return [{**dict(row), "details": json.loads(row["details_json"])} for row in rows]

    @staticmethod
    def _term_dict(row: sqlite3.Row) -> dict:
        result = dict(row)
        result["aliases"] = json.loads(result.pop("aliases_json"))
        return result

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _audit(db, admin_id, action, entity_type, entity_id, details) -> None:
        db.execute(
            """INSERT INTO admin_audit_log
               (admin_id, action, entity_type, entity_id, details_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (admin_id, action, entity_type, entity_id, json.dumps(details, ensure_ascii=False), _iso(_utc_now())),
        )


_database: AdminDatabase | None = None


def get_admin_database() -> AdminDatabase:
    global _database
    if _database is None:
        _database = AdminDatabase()
        _database.initialize()
    return _database
