from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.runner.db import Base

if TYPE_CHECKING:
    from .category_tag import CategoryTag
    from .reference import Reference


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    tags: Mapped[list["CategoryTag"]] = relationship(
        back_populates="category", cascade="all, delete", lazy="selectin"
    )
    references: Mapped[list["Reference"]] = relationship(
        back_populates="category", cascade="all, delete", lazy="selectin"
    )

    def __init__(self, name: str) -> None:
        self.name = name
