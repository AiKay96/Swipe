from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.personal_post.posts import Media as DomainMedia
from src.core.personal_post.posts import MediaType
from src.runner.db import Base

if TYPE_CHECKING:
    from .post import Post


class Media(Base):
    __tablename__ = "perosnal_post_media"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("personal_posts.id"))
    url: Mapped[str] = mapped_column(String)
    media_type: Mapped[str] = mapped_column(String)

    _post: Mapped[Post] = relationship(back_populates="media")

    def __init__(self, post_id: UUID, url: str, media_type: str):
        self.post_id = post_id
        self.url = url
        self.media_type = media_type

    def to_object(self) -> DomainMedia:
        return DomainMedia(
            id=self.id,
            url=self.url,
            media_type=MediaType(self.media_type),
        )
