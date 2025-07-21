from dataclasses import dataclass, field
from typing import Protocol
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

    def read_by_mail(self, mail: str) -> User | None:
        pass

    def read_by_username(self, username: str) -> User | None:
        pass
