from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.models.creator_post.category_tag import creator_post_category_tags
from src.infra.models.creator_post.hashtag import creator_post_hashtags
from src.runner.db import Base

if TYPE_CHECKING:
    from src.infra.models.user import User

    from .category import Category
    from .category_tag import CategoryTag
    from .comment import Comment
    from .hashtag import Hashtag
    from .like import Like
    from .media import Media
    from .reference import Reference
    from .save import Save


class Post(Base):
    __tablename__ = "creator_posts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    reference_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("references.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped[User] = relationship(back_populates="creator_posts")
    category: Mapped[Category] = relationship(back_populates="posts")
    reference: Mapped[Reference] = relationship(back_populates="posts")
    media: Mapped[list[Media]] = relationship(
        back_populates="_post", cascade="all, delete-orphan", lazy="selectin"
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="_post", cascade="all, delete-orphan", lazy="selectin"
    )
    _reactions: Mapped[list[Like]] = relationship(
        back_populates="_post", cascade="all, delete-orphan", lazy="selectin"
    )
    _saves: Mapped[list[Save]] = relationship(
        back_populates="_post", cascade="all, delete-orphan", lazy="selectin"
    )
    category_tags: Mapped[list[CategoryTag]] = relationship(
        secondary=creator_post_category_tags,
        back_populates="posts",
        lazy="selectin",
    )
    hashtags: Mapped[list[Hashtag]] = relationship(
        secondary=creator_post_hashtags,
        back_populates="posts",
        lazy="selectin",
    )
