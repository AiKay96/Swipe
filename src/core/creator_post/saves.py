from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class Save:
    post_id: UUID
    user_id: UUID
    id: UUID = field(default_factory=uuid4)


class SaveRepository(Protocol):
    def create(self, save: Save) -> Save: ...

    def get(self, user_id: UUID, post_id: UUID) -> Save | None: ...

    def get_user_saves_for_posts(
        self, user_id: UUID, post_ids: list[UUID]
    ) -> list[UUID]: ...

    def delete(self, save_id: UUID) -> None: ...
