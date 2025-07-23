from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from faker import Faker

from src.core.users import User

_faker = Faker()


@dataclass(frozen=True)
class FakeUser:
    mail: str = field(default_factory=lambda: _faker.email())
    password: str = field(default_factory=lambda: _faker.password())
    username: str = field(default_factory=lambda: _faker.unique.user_name())
    display_name: str = field(default_factory=lambda: _faker.unique.name())
    bio: str = field(default_factory=lambda: _faker.sentence(nb_words=10))
    id: UUID = field(default_factory=lambda: UUID(_faker.uuid4()))

    def as_dict(self) -> dict[str, Any]:
        return {
            "mail": self.mail,
            "password": self.password,
            "username": self.username,
            "display_name": self.display_name,
            "bio": self.bio,
        }

    def as_create_dict(self) -> dict[str, str]:
        return {
            "mail": self.mail,
            "password": self.password,
        }

    def as_user(self) -> User:
        return User(
            mail=self.mail,
            password=self.password,
            username=self.username,
            display_name=self.display_name,
            bio=self.bio,
        )
