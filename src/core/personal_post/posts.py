from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID, uuid4

from src.core.feed import FeedPost
from src.core.users import User

from .comments import Comment


class Privacy(str, Enum):
    PUBLIC = "public"
    FRIENDS_ONLY = "friends_only"


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


@dataclass
class Media:
    url: str
    media_type: MediaType
    id: UUID = field(default_factory=uuid4)


@dataclass
class Post:
    user_id: UUID
    user: User | None = None

    username: str | None = None
    description: str = ""
    like_count: int = 0
    dislike_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    privacy: Privacy = Privacy.FRIENDS_ONLY
    media: list[Media] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)


class PostRepository(Protocol):
    def create(self, post: Post) -> Post: ...

    def get(self, post_id: UUID) -> Post | None: ...

    def update_like_counts(
        self,
        post_id: UUID,
        like_count_delta: int = 0,
        dislike_count_delta: int = 0,
    ) -> None: ...

    def update_privacy(self, post_id: UUID, privacy: Privacy) -> None: ...

    def delete(self, post_id: UUID) -> None: ...

    def get_posts_by_user(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
        include_friends_only: bool = False,
    ) -> list[Post]: ...

    def get_posts_by_users(
        self, user_ids: list[UUID], before: datetime, limit: int
    ) -> list[Post]: ...


class PersonalPostService(Protocol):
    def create_post(
        self, user_id: UUID, description: str, media: list[Media]
    ) -> FeedPost: ...

    def change_privacy(self, user_id: UUID, post_id: UUID) -> None: ...

    def delete_post(self, post_id: UUID, user_id: UUID) -> None: ...

    def like_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def dislike_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def unlike_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def get_comments_by_post(self, post_id: UUID) -> list[Comment]: ...

    def comment_post(self, user_id: UUID, post_id: UUID, content: str) -> None: ...

    def remove_comment(
        self, post_id: UUID, comment_id: UUID, user_id: UUID
    ) -> None: ...

    def get_user_posts(
        self,
        user_id: UUID,
        from_user_id: UUID,
        limit: int,
        before: datetime,
    ) -> list[FeedPost]: ...
