from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.runner.db import Base

if TYPE_CHECKING:
    from src.infra.models.user import User

    from .personal_post import PersonalPost


class PostLike(Base):
    __tablename__ = "post_likes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("personal_posts.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    is_dislike: Mapped[bool] = mapped_column(Boolean, default=False)

    post: Mapped[PersonalPost] = relationship(back_populates="reactions")
    user: Mapped[User] = relationship(back_populates="post_likes")
