from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.runner.db import Base

if TYPE_CHECKING:
    from src.infra.models.user import User

    from .post_comment import PostComment
    from .post_like import PostLike
    from .post_media import PostMedia


class PersonalPost(Base):
    __tablename__ = "personal_posts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    like_count: Mapped[int] = mapped_column(Integer, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="personal_posts")
    media: Mapped[list[PostMedia]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    comments: Mapped[list[PostComment]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    reactions: Mapped[list[PostLike]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
