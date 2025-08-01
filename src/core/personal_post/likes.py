from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID, uuid4

from src.core.feed import Reaction


@dataclass
class Like:
    post_id: UUID
    user_id: UUID
    is_dislike: bool = False
    id: UUID = field(default_factory=uuid4)


class LikeRepository(Protocol):
    def create(self, like: Like) -> Like: ...

    def get(self, user_id: UUID, post_id: UUID) -> Like | None: ...

    def update(self, like_id: UUID, is_dislike: bool) -> None: ...

    def delete(self, like_id: UUID) -> None: ...

    def get_user_reactions(
        self, user_id: UUID, post_ids: list[UUID]
    ) -> dict[UUID, Reaction]: ...
