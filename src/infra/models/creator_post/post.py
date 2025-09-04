from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.creator_post.posts import Post as DomainPost
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

    category_tag_names: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    hashtag_names: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, default=0)

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

    def __init__(
        self,
        user_id: UUID,
        category_id: UUID | None,
        category_tag_names: list[str],
        hashtag_names: list[str],
        reference_id: UUID | None,
        description: str = "",
        like_count: int = 0,
        dislike_count: int = 0,
    ) -> None:
        self.user_id = user_id
        self.category_id = category_id
        self.reference_id = reference_id
        self.description = description
        self.like_count = like_count
        self.dislike_count = dislike_count
        self.category_tag_names = category_tag_names
        self.hashtag_names = hashtag_names

    def to_object(self) -> DomainPost:
        return DomainPost(
            id=self.id,
            user_id=self.user_id,
            category_id=self.category_id,
            reference_id=self.reference_id,
            description=self.description,
            created_at=self.created_at,
            like_count=self.like_count,
            dislike_count=self.dislike_count,
            media=[m.to_object() for m in self.media],
            comments=[c.to_object() for c in self.comments],
            category_tag_names=self.category_tag_names,
            hashtag_names=self.hashtag_names,
            category_name=self.category.name if self.category else None,
            reference_title=self.reference.title if self.reference else None,
            username=self.user.username,
            user=self.user.to_object() if self.user else None,
        )
