from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class PersonalPostLike:
    post_id: UUID
    user_id: UUID
    is_dislike: bool = False
    id: UUID = field(default_factory=uuid4)


class PersonalPostLikeRepository(Protocol):
    def create(self, like: PersonalPostLike) -> PersonalPostLike: ...
    def get_by_user_and_post(
        self, user_id: UUID, post_id: UUID
    ) -> PersonalPostLike | None: ...
    def update(self, like_id: UUID, is_dislike: bool) -> None: ...
    def delete(self, like_id: UUID) -> None: ...
