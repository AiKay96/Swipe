from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.users import User as DomainUser
from src.runner.db import Base

if TYPE_CHECKING:
    from .post.personal_post import PersonalPost
    from .post.post_comment import PostComment
    from .post.post_like import PostLike


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("mail"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    mail: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)
    bio: Mapped[str | None] = mapped_column(String)

    personal_posts: Mapped[list[PersonalPost]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    post_likes: Mapped[list[PostLike]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    post_comments: Mapped[list[PostComment]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        user_id: UUID,
        mail: str,
        hashed_password: str,
        username: str,
        display_name: str,
        bio: str | None = None,
    ) -> None:
        self.id = user_id
        self.mail = mail
        self.hashed_password = hashed_password
        self.username = username
        self.display_name = display_name
        self.bio = bio

    def to_object(self) -> DomainUser:
        return DomainUser(
            id=self.id,
            mail=self.mail,
            password=self.hashed_password,
            username=self.username,
            display_name=self.display_name,
            bio=self.bio,
        )
