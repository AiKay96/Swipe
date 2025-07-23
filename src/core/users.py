from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID, uuid4


@dataclass
class User:
    mail: str
    password: str
    username: str
    display_name: str
    bio: str | None = None

    id: UUID = field(default_factory=uuid4)


class UserRepository(Protocol):
    def create(self, user: User) -> User:
        pass

    def read_by(
        self,
        *,
        user_id: UUID | None = None,
        mail: str | None = None,
        username: str | None = None,
    ) -> User | None:
        pass

    def find_by_username(self, username: str) -> User | None:
        pass

    def update(self, user_id: UUID, updates: dict[str, Any]) -> None:
        pass
