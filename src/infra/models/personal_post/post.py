from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.personal_post.posts import Post as DomainPost
from src.core.personal_post.posts import Privacy
from src.runner.db import Base

if TYPE_CHECKING:
    from src.infra.models.user import User

    from .comment import Comment
    from .like import Like
    from .media import Media


class Post(Base):
    __tablename__ = "personal_posts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    privacy: Mapped[str] = mapped_column(String)

    like_count: Mapped[int] = mapped_column(Integer, default=0)
    dislike_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="personal_posts")
    media: Mapped[list[Media]] = relationship(
        back_populates="_post", cascade="all, delete-orphan"
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="_post", cascade="all, delete-orphan"
    )
    _reactions: Mapped[list[Like]] = relationship(
        back_populates="_post", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        user_id: UUID,
        description: str = "",
        like_count: int = 0,
        dislike_count: int = 0,
        privacy: Privacy = Privacy.FRIENDS_ONLY,
    ) -> None:
        self.user_id = user_id
        self.description = description
        self.like_count = like_count
        self.dislike_count = dislike_count
        self.privacy = privacy.value

    def to_object(self) -> DomainPost:
        return DomainPost(
            id=self.id,
            user_id=self.user_id,
            description=self.description,
            created_at=self.created_at,
            privacy=Privacy(self.privacy),
            like_count=self.like_count,
            dislike_count=self.dislike_count,
            media=[m.to_object() for m in self.media],
            comments=[c.to_object() for c in self.comments],
        )
