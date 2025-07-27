from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.users import User as DomainUser
from src.runner.db import Base

if TYPE_CHECKING:
    from .personal_post.comment import PersonalComment as PersonalComment
    from .personal_post.like import PersonalLike as PersonalLike
    from .personal_post.post import PersonalPost as PersonalPost

from .creator_post.comment import Comment as CreatorComment
from .creator_post.like import Like as CreatorLike
from .creator_post.post import Post as CreatorPost
from .creator_post.save import Save as CreatorSave


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("mail"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    mail: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)
    bio: Mapped[str | None] = mapped_column(String)

    personal_posts: Mapped[list[PersonalPost]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    _personal_post_likes: Mapped[list[PersonalLike]] = relationship(
        back_populates="_user", cascade="all, delete-orphan", lazy="selectin"
    )
    _personal_post_comments: Mapped[list[PersonalComment]] = relationship(
        back_populates="_user", cascade="all, delete-orphan", lazy="selectin"
    )
    creator_posts: Mapped[list[CreatorPost]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    _creator_post_likes: Mapped[list[CreatorLike]] = relationship(
        back_populates="_user", cascade="all, delete-orphan", lazy="selectin"
    )
    _creator_post_comments: Mapped[list[CreatorComment]] = relationship(
        back_populates="_user", cascade="all, delete-orphan", lazy="selectin"
    )
    _creator_post_saves: Mapped[list[CreatorSave]] = relationship(
        back_populates="_user", cascade="all, delete-orphan", lazy="selectin"
    )

    def __init__(
        self,
        mail: str,
        hashed_password: str,
        username: str,
        display_name: str,
        bio: str | None = None,
    ) -> None:
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
