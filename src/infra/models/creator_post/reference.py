from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.models.creator_post.category_tag import reference_category_tags
from src.runner.db import Base

if TYPE_CHECKING:
    from .category import Category
    from .category_tag import CategoryTag


class Reference(Base):
    __tablename__ = "references"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, default="")
    image_url: Mapped[str] = mapped_column(String, default="")
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    category: Mapped["Category"] = relationship(back_populates="references")
    tags: Mapped[list["CategoryTag"]] = relationship(
        secondary=reference_category_tags,
        back_populates="references",
        lazy="selectin",
    )

    def __init__(
        self,
        category_id: UUID,
        title: str,
        description: str = "",
        image_url: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.category_id = category_id
        self.title = title
        self.description = description
        self.image_url = image_url
        self.attributes = attributes or {}
