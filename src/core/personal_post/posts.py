from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class Post:
    user_id: UUID
    description: str = ""
    like_count: int = 0
    dislike_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: UUID = field(default_factory=uuid4)


class PostRepository(Protocol):
    def create(self, post: Post) -> Post: ...
    def get_by_id(self, post_id: UUID) -> Post | None: ...
    def list_by_user(self, user_id: UUID) -> list[Post]: ...
    def update_like_counts(
        self, post_id: UUID, like_count: int, dislike_count: int
    ) -> None: ...
    def delete(self, post_id: UUID) -> None: ...
