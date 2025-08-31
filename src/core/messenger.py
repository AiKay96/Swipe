from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class Chat:
    id: UUID = field(default_factory=uuid4)
    user_a_id: UUID = field(default_factory=uuid4)
    user_b_id: UUID = field(default_factory=uuid4)
    last_message_at: datetime | None = None
    last_message_id: UUID | None = None


@dataclass
class Message:
    id: UUID = field(default_factory=uuid4)
    chat_id: UUID = field(default_factory=uuid4)
    sender_id: UUID = field(default_factory=uuid4)
    body: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    seen_at_user_a: datetime | None = None
    seen_at_user_b: datetime | None = None


@dataclass
class ChatSummary:
    chat: Chat
    peer_id: UUID
    unread_count: int
    last_body: str | None


class MessengerService(Protocol):
    def get_or_start_chat(self, user_id: UUID, peer_id: UUID) -> Chat: ...

    def send_message(self, sender_id: UUID, peer_id: UUID, body: str) -> Message: ...

    def get_inbox(
        self,
        user_id: UUID,
        *,
        limit: int = 30,
        before: datetime | None = None,
    ) -> list[ChatSummary]: ...

    def get_messages(
        self,
        user_id: UUID,
        peer_id: UUID | None = None,
        chat_id: UUID | None = None,
        *,
        limit: int = 50,
        before: datetime | None = None,
        mark_seen: bool = True,
    ) -> list[Message]: ...

    def mark_chat_seen(self, user_id: UUID, chat_id: UUID) -> int: ...
