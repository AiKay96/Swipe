from uuid import UUID

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from src.runner.db import Base


class FeedPreference(Base):
    __tablename__ = "feed_preferences"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id"), primary_key=True
    )
    points: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        Index("ix_feed_preferences_user_cat_tag", "user_id", "category_id"),
    )

    def __init__(
        self,
        user_id: UUID,
        category_id: UUID,
        points: int = 0,
    ):
        self.user_id = user_id
        self.category_id = category_id
        self.points = points
