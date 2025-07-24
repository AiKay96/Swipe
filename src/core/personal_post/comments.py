from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class Comment:
    post_id: UUID
    user_id: UUID
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: UUID = field(default_factory=uuid4)


class CommentRepository(Protocol):
    def create(self, comment: Comment) -> Comment: ...
    def get_by_post(self, post_id: UUID) -> list[Comment]: ...
    def delete(self, comment_id: UUID) -> None: ...
