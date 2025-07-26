from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.personal_post.comments import (
    Comment as DomainPersonalPostComment,
)
from src.runner.db import Base

if TYPE_CHECKING:
    from src.infra.models.user import User

    from .post import Post


class Comment(Base):
    __tablename__ = "perosnal_post_comments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("personal_posts.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    _post: Mapped[Post] = relationship(back_populates="comments")
    _user: Mapped[User] = relationship(back_populates="_post_comments")

    def __init__(
        self,
        post_id: UUID,
        user_id: UUID,
        content: str,
    ) -> None:
        self.post_id = post_id
        self.user_id = user_id
        self.content = content

    def to_object(self) -> DomainPersonalPostComment:
        return DomainPersonalPostComment(
            id=self.id,
            post_id=self.post_id,
            user_id=self.user_id,
            content=self.content,
            created_at=self.created_at,
        )
