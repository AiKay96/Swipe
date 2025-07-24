from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from .comments import Comment
from .medias import Media


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
    def list_by_user(self, user_id: UUID) -> list[Post]: ...
    def update_like_counts(
        self,
        post_id: UUID,
        like_count_delta: int = 0,
        dislike_count_delta: int = 0,
    ) -> None: ...
    def delete(self, post_id: UUID) -> None: ...
