from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.runner.db import Base


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    from_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    to_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    def __init__(self, from_user_id: UUID, to_user_id: UUID):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id


class Friend(Base):
    __tablename__ = "friends"
    __table_args__ = (UniqueConstraint("user_id", "friend_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    friend_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    def __init__(self, user_id: UUID, friend_id: UUID):
        self.user_id = user_id
        self.friend_id = friend_id


class SuggestionSkip(Base):
    __tablename__ = "suggestion_skips"
    __table_args__ = (UniqueConstraint("user_id", "target_user_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    skipped_at: Mapped[datetime] = mapped_column(default=datetime.now)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def __init__(self, user_id: UUID, target_user_id: UUID, expires_at: datetime):
        self.user_id = user_id
        self.target_user_id = target_user_id
        self.expires_at = expires_at
