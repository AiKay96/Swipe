from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class PersonalPost:
    user_id: UUID
    description: str = ""
    like_count: int = 0
    dislike_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: UUID = field(default_factory=uuid4)


class PersonalPostRepository(Protocol):
    def create(self, post: PersonalPost) -> PersonalPost: ...
    def get_by_id(self, post_id: UUID) -> PersonalPost | None: ...
    def list_by_user(self, user_id: UUID) -> list[PersonalPost]: ...
    def update_like_counts(
        self, post_id: UUID, like_count: int, dislike_count: int
    ) -> None: ...
    def delete(self, post_id: UUID) -> None: ...
