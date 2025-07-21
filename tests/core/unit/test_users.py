from typing import Any

import pytest

from src.core.errors import ExistsError
from src.infra.repositories.users import UserRepository
from tests.fake import FakeUser


def test_should_not_read_unknown_user(db_session: Any) -> None:
    repo = UserRepository(db_session)

    assert repo.read_by_mail(FakeUser().as_user().mail) is None


def test_should_persist(db_session: Any) -> None:
    repo = UserRepository(db_session)
    user = FakeUser().as_user()

    repo.create(user)
    db_user = repo.read_by_mail(user.mail)

    assert db_user is not None
    assert db_user.mail == user.mail
    assert db_user.id == user.id


def test_should_not_create(db_session: Any) -> None:
    repo = UserRepository(db_session)

    user = FakeUser().as_user()
    repo.create(user)

    with pytest.raises(ExistsError):
        repo.create(user)
