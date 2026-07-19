"""Validated API contracts for glossary administration."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


GlossaryStatus = Literal["draft", "linguistic_review", "medical_review", "approved", "rejected"]


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    username: str


class AdminIdentity(BaseModel):
    id: int
    username: str
    expires_at: datetime


class GlossaryTermCreate(BaseModel):
    french: str = Field(min_length=1, max_length=160)
    arabic: str = Field(min_length=1, max_length=160)
    latin: str = Field(min_length=1, max_length=160)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    status: GlossaryStatus = "draft"
    notes: str = Field(default="", max_length=2000)

    @field_validator("aliases")
    @classmethod
    def normalize_aliases(cls, aliases: list[str]) -> list[str]:
        cleaned = []
        for alias in aliases:
            value = alias.strip()
            if value and value not in cleaned:
                cleaned.append(value)
        return cleaned


class GlossaryTermUpdate(BaseModel):
    french: str | None = Field(default=None, min_length=1, max_length=160)
    arabic: str | None = Field(default=None, min_length=1, max_length=160)
    latin: str | None = Field(default=None, min_length=1, max_length=160)
    aliases: list[str] | None = Field(default=None, max_length=30)
    status: GlossaryStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("aliases")
    @classmethod
    def normalize_aliases(cls, aliases: list[str] | None) -> list[str] | None:
        return GlossaryTermCreate.normalize_aliases(aliases) if aliases is not None else None


class GlossaryTermResponse(BaseModel):
    id: int
    french: str
    arabic: str
    latin: str
    aliases: list[str]
    status: GlossaryStatus
    notes: str
    created_by: int | None
    updated_by: int | None
    approved_by: int | None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None


class AuditLogResponse(BaseModel):
    id: int
    admin_id: int | None
    username: str | None
    action: str
    entity_type: str
    entity_id: int | None
    details: dict
    created_at: datetime
    details_json: str = Field(exclude=True)
