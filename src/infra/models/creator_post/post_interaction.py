from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.runner.db import Base


class PostInteraction(Base):
    __tablename__ = "creator_post_interactions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    post_id: Mapped[UUID] = mapped_column(
        ForeignKey("creator_posts.id"), primary_key=True
    )
    last_interacted_at = Column(
        DateTime, default=datetime.now(), onupdate=datetime.now(), nullable=False
    )

    def __init__(self, user_id: UUID, post_id: UUID):
        self.user_id = user_id
        self.post_id = post_id
