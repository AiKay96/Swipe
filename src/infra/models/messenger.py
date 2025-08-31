from datetime import datetime
from tokenize import String
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.messenger import Chat as DomainChat
from src.core.messenger import Message as DomainMessage
from src.runner.db import Base


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_a_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user_b_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    last_message_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_message_id: Mapped[UUID | None] = mapped_column(nullable=True)

    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_chat_pair"),)

    def __init__(
        self,
        user_a_id: UUID,
        user_b_id: UUID,
        last_message_at: datetime | None = None,
        last_message_id: UUID | None = None,
    ) -> None:
        self.user_a_id = user_a_id
        self.user_b_id = user_b_id
        self.last_message_at = last_message_at
        self.last_message_id = last_message_id

    def to_object(self) -> DomainChat:
        return DomainChat(
            id=self.id,
            user_a_id=self.user_a_id,
            user_b_id=self.user_b_id,
            last_message_at=self.last_message_at,
            last_message_id=self.last_message_id,
        )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    body: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    seen_at_user_a: Mapped[datetime | None] = mapped_column(DateTime)
    seen_at_user_b: Mapped[datetime | None] = mapped_column(DateTime)

    def __init__(
        self,
        chat_id: UUID,
        sender_id: UUID,
        body: str,
        created_at: datetime | None = None,
        seen_at_user_a: datetime | None = None,
        seen_at_user_b: datetime | None = None,
    ) -> None:
        self.chat_id = chat_id
        self.sender_id = sender_id
        self.body = body
        self.created_at = created_at or datetime.utcnow()
        self.seen_at_user_a = seen_at_user_a
        self.seen_at_user_b = seen_at_user_b

    def to_object(self) -> DomainMessage:
        return DomainMessage(
            id=self.id,
            chat_id=self.chat_id,
            sender_id=self.sender_id,
            body=self.body,
            created_at=self.created_at,
            seen_at_user_a=self.seen_at_user_a,
            seen_at_user_b=self.seen_at_user_b,
        )
