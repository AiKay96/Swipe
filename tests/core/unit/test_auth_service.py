from dataclasses import dataclass
from typing import Any
from uuid import UUID

import bcrypt
import pytest

from src.core.errors import DoesNotExistError
from src.core.users import User
from src.infra.services.auth import AuthService
from tests.fake import FakeUser


def test_should_decode_valid_access_token() -> None:
    repo = FakeRepo([])
    service = AuthService(repo)

    user = FakeUser()
    token = service.create_access_token(user.username)
    username = service.decode_token(token)

    assert username == user.username


def test_should_fail_on_invalid_token() -> None:
    repo = FakeRepo([])
    service = AuthService(repo)

    with pytest.raises(DoesNotExistError):
        service.decode_token("invalid.token")


def test_should_fail_on_token_type_mismatch() -> None:
    repo = FakeRepo([])
    service = AuthService(repo)

    token = service.create_refresh_token(FakeUser().username)

    with pytest.raises(DoesNotExistError):
        service.decode_token(token, expected_type="access")


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
        service.authenticate(user.username, FakeUser().username)


def test_should_get_user_from_valid_token() -> None:
    user = FakeUser().as_user()
    repo = FakeRepo([user])
    service = AuthService(repo)

    token = service.create_access_token(user.username)
    result = service.get_user_from_token(token)

    assert result.username == user.username


def test_should_fail_get_user_from_token_when_user_missing() -> None:
    repo = FakeRepo([])
    service = AuthService(repo)

    token = service.create_access_token(FakeUser().username)

    with pytest.raises(DoesNotExistError):
        service.get_user_from_token(token)


def test_should_refresh_access_token() -> None:
    user = FakeUser().as_user()
    repo = FakeRepo([user])
    service = AuthService(repo)

    refresh = service.create_refresh_token(user.username)
    access = service.refresh_access_token(refresh)

    assert isinstance(access, str)


@dataclass
class FakeRepo:
    users: list[User]

    def find_by_username(self, username: str) -> User | None:
        for u in self.users:
            if u.username == username:
                return u
        return None

    def read_by(
        self,
        *,
        user_id: UUID | None = None,  # noqa ARG002
        mail: str | None = None,  # noqa ARG002
        username: str | None = None,  # noqa ARG002
    ) -> User | None:
        return None

    def create(self, user: User) -> User:
        return user

    def update(self, user_id: UUID, updates: dict[str, Any]) -> None:  # noqa ARG002
        pass
