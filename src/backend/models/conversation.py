"""
In-memory conversation store.

For this academic prototype, conversations live in server memory (keyed by
UUID). This keeps the stack simple while still giving the frontend a real
`conversation_id` to build history around. Swapping this for PostgreSQL later
only requires changing `ConversationRepository`'s internals — its interface
stays the same, so nothing above it (services, routers) needs to change.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional

from src.backend.schemas.chat import ConversationMessage


@dataclass
class Conversation:
    id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


class ConversationRepository:
    """Thread-safe in-memory repository for conversations."""

    def __init__(self) -> None:
        self._conversations: Dict[str, Conversation] = {}
        self._lock = Lock()

    def create(self) -> Conversation:
        conv = Conversation(id=str(uuid.uuid4()))
        with self._lock:
            self._conversations[conv.id] = conv
        return conv

    def get(self, conversation_id: str) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    def get_or_create(self, conversation_id: Optional[str]) -> Conversation:
        if conversation_id:
            conv = self.get(conversation_id)
            if conv:
                return conv
        return self.create()

    def add_message(self, conversation_id: str, message: ConversationMessage) -> None:
        with self._lock:
            conv = self._conversations.get(conversation_id)
            if conv is None:
                raise KeyError(f"Unknown conversation_id: {conversation_id}")
            conv.messages.append(message)


_repository_instance: "ConversationRepository | None" = None


def get_conversation_repository() -> ConversationRepository:
    """Singleton accessor used as a FastAPI dependency."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = ConversationRepository()
    return _repository_instance
