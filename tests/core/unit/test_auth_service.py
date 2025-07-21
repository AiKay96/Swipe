from dataclasses import dataclass

import bcrypt
import pytest

from src.core.errors import DoesNotExistError
from src.core.users import User
from src.infra.services.auth import AuthService
from tests.fake import FakeUser


def test_should_authenticate_and_generate_tokens() -> None:
    fake = FakeUser()
    raw_password = fake.password

    user = fake.as_user()
    user.password = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    repo = FakeRepo([user])
    service = AuthService(repo)

    access, refresh = service.authenticate(user.username, raw_password)

    assert isinstance(access, str)
    assert isinstance(refresh, str)


def test_should_fail_auth_on_wrong_password() -> None:
    user = FakeUser().as_user()
    user.password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

    repo = FakeRepo([user])
    service = AuthService(repo)

    with pytest.raises(DoesNotExistError):
        service.authenticate(user.username, "wrong")


@dataclass
class FakeRepo:
    users: list[User]

    def read_by_username(self, username: str) -> User | None:
        for u in self.users:
            if u.username == username:
                return u
        return None

    def read_by_mail(self, mail: str) -> User | None:  # noqa ARG002
        return None

    def create(self, user: User) -> User:
        return user
