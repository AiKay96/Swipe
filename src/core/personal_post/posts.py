from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID, uuid4

from .comments import Comment


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
    description: str = ""
    like_count: int = 0
    dislike_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
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
    def delete(self, post_id: UUID) -> None: ...


class PersonalPostService(Protocol):
    def create_post(
        self, user_id: UUID, description: str, media: list[Media]
    ) -> Post: ...

    def delete_post(self, post_id: UUID, user_id: UUID) -> None: ...

    def like_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def dislike_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def unlike_post(self, user_id: UUID, post_id: UUID) -> None: ...

    def comment_post(self, user_id: UUID, post_id: UUID, content: str) -> None: ...

    def remove_comment(
        self, post_id: UUID, comment_id: UUID, user_id: UUID
    ) -> None: ...
