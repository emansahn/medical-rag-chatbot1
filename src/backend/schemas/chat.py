"""Request/response schemas for the /chat endpoints."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

ResponseLanguage = Literal["fr", "ary", "ary-arab", "ary-latn"]


class ChatRequest(BaseModel):
    """Payload sent by the frontend for a new chat message."""

    question: str = Field(..., min_length=1, max_length=2000, description="User's medical question.")
    conversation_id: Optional[str] = Field(None, description="Existing conversation to append to.")
    language: ResponseLanguage = Field(
        "fr",
        description="Response language: French, Darija Arabic script, or Darija Latin script.",
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question must not be empty or whitespace only.")
        return v.strip()


class SourceCitationSchema(BaseModel):
    title: str
    url: str
    excerpt: str


class ChatResponse(BaseModel):
    """Response returned to the frontend for a chat message."""

    conversation_id: str
    answer: str
    sources: List[SourceCitationSchema] = Field(default_factory=list)
    is_stub: bool = Field(..., description="True while the real RAG engine is not yet wired in.")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    sources: List[SourceCitationSchema] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
