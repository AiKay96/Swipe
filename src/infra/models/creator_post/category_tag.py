from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.runner.db import Base

reference_category_tags = Table(
    "reference_category_tags",
    Base.metadata,
    Column(
        "reference_id",
        ForeignKey("references.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", ForeignKey("category_tags.id", ondelete="CASCADE"), primary_key=True
    ),
)

creator_post_category_tags = Table(
    "creator_post_category_tags",
    Base.metadata,
    Column(
        "post_id", ForeignKey("creator_posts.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "tag_id", ForeignKey("category_tags.id", ondelete="CASCADE"), primary_key=True
    ),
)

if TYPE_CHECKING:
    from .category import Category
    from .post import Post
    from .reference import Reference


class CategoryTag(Base):
    __tablename__ = "category_tags"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

    category: Mapped[Category] = relationship(back_populates="tags")
    references: Mapped[list[Reference]] = relationship(
        secondary=reference_category_tags, back_populates="tags", lazy="selectin"
    )

    posts: Mapped[list[Post]] = relationship(
        secondary=creator_post_category_tags,
        back_populates="category_tags",
        lazy="selectin",
    )

    def __init__(self, category_id: UUID, name: str) -> None:
        self.category_id = category_id
        self.name = name
