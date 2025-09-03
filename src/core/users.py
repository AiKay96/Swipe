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
    def create(self, user: User) -> User: ...

    def read_by(
        self,
        *,
        user_id: UUID | None = None,
        mail: str | None = None,
        username: str | None = None,
    ) -> User | None: ...

    def find_by_username(self, username: str) -> User | None: ...

    def update(self, user_id: UUID, updates: dict[str, Any]) -> None: ...

    def read_many_by_ids(self, ids: list[UUID]) -> list[User]: ...


class UserService(Protocol):
    def register(self, mail: str, password: str) -> User: ...

    def get_by_mail(self, mail: str) -> User: ...

    def get_by_username(self, username: str) -> User: ...

    def update_user(
        self,
        user_id: UUID,
        *,
        username: str | None = None,
        display_name: str | None = None,
        bio: str | None = None,
    ) -> None: ...

    def generate_unique_username(self) -> str: ...
