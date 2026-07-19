"""Authenticated administration endpoints for the controlled Darija glossary."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.admin.database import GLOSSARY_STATUSES, AdminDatabase, get_admin_database
from src.backend.schemas.admin import (
    AdminIdentity,
    AdminLoginRequest,
    AdminLoginResponse,
    AuditLogResponse,
    GlossaryTermCreate,
    GlossaryTermResponse,
    GlossaryTermUpdate,
)

router = APIRouter(prefix="/admin", tags=["Glossary administration"])
bearer = HTTPBearer(auto_error=False)


def _credentials(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Administrator authentication required.")
    return credentials.credentials


def get_admin(
    token: Annotated[str, Depends(_credentials)],
    database: Annotated[AdminDatabase, Depends(get_admin_database)],
) -> dict:
    admin = database.admin_for_token(token)
    if not admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired administrator session.")
    return admin


@router.post("/auth/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest, database: Annotated[AdminDatabase, Depends(get_admin_database)]):
    authenticated = database.authenticate(payload.username, payload.password)
    if not authenticated:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid administrator credentials.")
    token, admin = authenticated
    return AdminLoginResponse(
        access_token=token,
        username=admin["username"],
        expires_at=admin["expires_at"],
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: Annotated[str, Depends(_credentials)],
    admin: Annotated[dict, Depends(get_admin)],
    database: Annotated[AdminDatabase, Depends(get_admin_database)],
) -> Response:
    database.logout(token, admin["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/me", response_model=AdminIdentity)
def me(admin: Annotated[dict, Depends(get_admin)]) -> dict:
    return admin


@router.get("/glossary", response_model=list[GlossaryTermResponse])
def list_glossary(
    admin: Annotated[dict, Depends(get_admin)],
    database: Annotated[AdminDatabase, Depends(get_admin_database)],
    term_status: str | None = Query(default=None, alias="status"),
    search: str = Query(default="", max_length=160),
) -> list[dict]:
    del admin
    if term_status and term_status not in GLOSSARY_STATUSES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown glossary status.")
    return database.list_terms(term_status, search)


@router.post("/glossary", response_model=GlossaryTermResponse, status_code=status.HTTP_201_CREATED)
def create_glossary_term(
    payload: GlossaryTermCreate,
    admin: Annotated[dict, Depends(get_admin)],
    database: Annotated[AdminDatabase, Depends(get_admin_database)],
) -> dict:
    try:
        return database.create_term(payload.model_dump(), admin["id"])
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "This French term already exists.") from exc


@router.put("/glossary/{term_id}", response_model=GlossaryTermResponse)
def update_glossary_term(
    term_id: int,
    payload: GlossaryTermUpdate,
    admin: Annotated[dict, Depends(get_admin)],
    database: Annotated[AdminDatabase, Depends(get_admin_database)],
) -> dict:
    try:
        term = database.update_term(term_id, payload.model_dump(exclude_unset=True), admin["id"])
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "This French term already exists.") from exc
    if not term:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Glossary term not found.")
    return term


@router.delete("/glossary/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_term(
    term_id: int,
    admin: Annotated[dict, Depends(get_admin)],
    database: Annotated[AdminDatabase, Depends(get_admin_database)],
) -> Response:
    if not database.delete_term(term_id, admin["id"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Glossary term not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audit", response_model=list[AuditLogResponse])
def audit_log(
    admin: Annotated[dict, Depends(get_admin)],
    database: Annotated[AdminDatabase, Depends(get_admin_database)],
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    del admin
    return database.audit_log(limit)
