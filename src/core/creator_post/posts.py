from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID, uuid4

from src.core.feed import FeedPost

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

    category_id: UUID | None = None
    category_name: str | None = None
    reference_id: UUID | None = None
    reference_title: str | None = None
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    like_count: int = 0
    dislike_count: int = 0

    category_tag_names: list[str] = field(default_factory=list)
    hashtag_names: list[str] = field(default_factory=list)

    media: list[Media] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    username: str | None = None

    id: UUID = field(default_factory=uuid4)


class PostRepository(Protocol):
    def create(self, post: Post) -> Post: ...

    def get(self, post_id: UUID) -> Post | None: ...

    def batch_get(self, ids: list[UUID]) -> list[Post]: ...

    def update_like_counts(
        self,
        post_id: UUID,
        like_count_delta: int = 0,
        dislike_count_delta: int = 0,
    ) -> None: ...

    def delete(self, post_id: UUID) -> None: ...

    def get_posts_by_user(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
    ) -> list[Post]: ...

    def get_posts_by_users(
        self, user_ids: list[UUID], before: datetime, limit: int
    ) -> list[Post]: ...

    def get_saved_posts_by_user(
        self, user_id: UUID, limit: int, before: datetime
    ) -> list[Post]: ...

    def get_posts_by_users_in_category(
        self,
        user_ids: list[UUID],
        category_id: UUID,
        exclude_ids: list[UUID],
        limit: int,
        before: datetime,
    ) -> list[Post]: ...

    def get_trending_posts_in_category(
        self,
        category_id: UUID,
        exclude_user_ids: list[UUID],
        exclude_post_ids: list[UUID],
        limit: int,
        days: int = 30,
    ) -> list[Post]: ...


class CreatorPostService(Protocol):
    def create_post(
        self,
        user_id: UUID,
        category_id: UUID,
        reference_id: UUID | None,
        description: str,
        category_tag_names: list[str],
        hashtag_names: list[str],
        media: list[Media],
    ) -> FeedPost: ...

    def delete_post(self, post_id: UUID, user_id: UUID) -> None: ...

    def like_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def dislike_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def unlike_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def get_comments_by_post(self, post_id: UUID) -> list[Comment]: ...

    def comment_post(self, user_id: UUID, post_id: UUID, content: str) -> None: ...

    def remove_comment(
        self, post_id: UUID, comment_id: UUID, user_id: UUID
    ) -> None: ...

    def save_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def remove_save(self, user_id: UUID, post_id: UUID) -> None: ...

    def get_user_posts(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
    ) -> list[FeedPost]: ...

    def get_user_saves(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
    ) -> list[FeedPost]: ...
