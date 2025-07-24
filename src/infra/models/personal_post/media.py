from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.runner.db import Base

if TYPE_CHECKING:
    from .post import Post


class Media(Base):
    __tablename__ = "post_media"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("personal_posts.id"))
    url: Mapped[str] = mapped_column(String)
    post_type: Mapped[str] = mapped_column(String)  # "image" or "video"

    post: Mapped[Post] = relationship(back_populates="media")
