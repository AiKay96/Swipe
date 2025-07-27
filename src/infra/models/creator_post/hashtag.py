from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.runner.db import Base

creator_post_hashtags = Table(
    "creator_post_hashtags",
    Base.metadata,
    Column(
        "post_id", ForeignKey("creator_posts.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("tag_id", ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True),
)

if TYPE_CHECKING:
    from .post import Post


class Hashtag(Base):
    __tablename__ = "hashtags"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    posts: Mapped[list["Post"]] = relationship(
        secondary=creator_post_hashtags, back_populates="hashtags", lazy="selectin"
    )

    def __init__(self, name: str) -> None:
        self.name = name
