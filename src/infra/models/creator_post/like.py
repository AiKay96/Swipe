from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.creator_post.likes import Like as DomainLike
from src.runner.db import Base

if TYPE_CHECKING:
    from src.infra.models.user import User

    from .post import Post


class Like(Base):
    __tablename__ = "creator_post_likes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("creator_posts.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    is_dislike: Mapped[bool] = mapped_column(Boolean, default=False)

    _post: Mapped[Post] = relationship(back_populates="_reactions")
    _user: Mapped[User] = relationship(back_populates="_creator_post_likes")

    def __init__(
        self,
        post_id: UUID,
        user_id: UUID,
        is_dislike: bool,
    ) -> None:
        self.post_id = post_id
        self.user_id = user_id
        self.is_dislike = is_dislike

    def to_object(self) -> DomainLike:
        return DomainLike(
            id=self.id,
            post_id=self.post_id,
            user_id=self.user_id,
            is_dislike=self.is_dislike,
        )
