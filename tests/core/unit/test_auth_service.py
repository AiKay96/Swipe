from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

import bcrypt
import pytest

from src.core.errors import DoesNotExistError
from src.core.users import User
from src.infra.services.auth import AuthService
from tests.fake import FakeUser


def test_should_decode_valid_access_token() -> None:
    repo = FakeUserRepo([])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    user = FakeUser()
    token = service.create_access_token(str(user.id))
    user_id = service.decode_token(token)["sub"]

    assert user_id == str(user.id)


def test_should_fail_on_invalid_token() -> None:
    repo = FakeUserRepo([])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    with pytest.raises(DoesNotExistError):
        service.decode_token("invalid.token")


def test_should_fail_on_token_type_mismatch() -> None:
    repo = FakeUserRepo([])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    token = service.create_refresh_token(str(FakeUser().id))

    with pytest.raises(DoesNotExistError):
        service.decode_token(token, expected_type="access")


def test_should_authenticate_and_generate_tokens() -> None:
    fake = FakeUser()
    raw_password = fake.password

    user = fake.as_user()
    user.password = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    repo = FakeUserRepo([user])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    access, refresh = service.authenticate(user.username, raw_password)

    assert isinstance(access, str)
    assert isinstance(refresh, str)


def test_should_fail_auth_on_wrong_password() -> None:
    user = FakeUser().as_user()
    user.password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

    repo = FakeUserRepo([user])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    with pytest.raises(DoesNotExistError):
        service.authenticate(user.username, "wrong-password")


def test_should_get_user_from_valid_token() -> None:
    user = FakeUser().as_user()
    repo = FakeUserRepo([user])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    token = service.create_access_token(str(user.id))
    result = service.get_user_from_token(token)

    assert result.username == user.username


def test_should_fail_get_user_from_token_when_user_missing() -> None:
    repo = FakeUserRepo([])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    token = service.create_access_token(str(FakeUser().id))

    with pytest.raises(DoesNotExistError):
        service.get_user_from_token(token)


def test_should_refresh_access_token() -> None:
    user = FakeUser().as_user()
    repo = FakeUserRepo([user])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    refresh = service.create_refresh_token(str(user.id))
    access = service.refresh_access_token(refresh)

    assert isinstance(access, str)


def test_should_not_validate_logged_out_refresh_token() -> None:
    user = FakeUser().as_user()
    repo = FakeUserRepo([user])
    tokens = FakeTokenRepo()
    service = AuthService(repo, tokens)

    refresh_token = service.create_refresh_token(str(user.id))

    payload = service.decode_token(refresh_token, expected_type="refresh")
    jti = UUID(payload["jti"])
    tokens.delete(jti)

    with pytest.raises(DoesNotExistError):
        service.refresh_access_token(refresh_token)


@dataclass
class FakeUserRepo:
    users: list[User]

    def find_by_username(self, username: str) -> User | None:
        for u in self.users:
            if u.username == username:
                return u
        return None

    def read_by(
        self,
        *,
        user_id: UUID | None = None,
        mail: str | None = None,  # noqa: ARG002
        username: str | None = None,  # noqa: ARG002
    ) -> User | None:
        for u in self.users:
            if user_id and u.id == user_id:
                return u
        return None

    def create(self, user: User) -> User:
        return user

    def update(self, user_id: UUID, updates: dict[str, Any]) -> None:  # noqa: ARG002
        pass


@dataclass
class FakeTokenRepo:
    db: dict[UUID, UUID] = field(default_factory=dict)

    def save(self, jti: UUID, user_id: UUID, expires_at: datetime) -> None:  # noqa: ARG002
        self.db[jti] = user_id

    def exists(self, jti: UUID) -> bool:
        return jti in self.db

    def delete(self, jti: UUID) -> None:
        self.db.pop(jti, None)
