from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.runner.db import Base

if TYPE_CHECKING:
    from src.infra.models.user import User

    from .post import Post


class Save(Base):
    __tablename__ = "creator_post_saves"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("creator_posts.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    _post: Mapped[Post] = relationship(back_populates="_saves")
    _user: Mapped[User] = relationship(back_populates="_creator_post_saves")

    def __init__(
        self,
        post_id: UUID,
        user_id: UUID,
    ) -> None:
        self.post_id = post_id
        self.user_id = user_id
