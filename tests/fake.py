from dataclasses import dataclass, field
from typing import Any

from faker import Faker

from src.core.users import User


@dataclass
class Fake:
    faker: Faker = field(default_factory=Faker)

    def user_dict(self) -> dict[str, Any]:
        return {
            "mail": self.faker.email(),
            "password": self.faker.password(),
        }

    def user(self) -> User:
        data = self.user_dict()
        return User(**data)
