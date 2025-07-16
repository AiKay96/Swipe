from typing import Any

import pytest

from src.core.errors import DoesNotExistError, ExistsError
from src.infra.repositories.users import UserRepository
from tests.fake import Fake


def test_should_not_read_unknown_user(db_session: Any) -> None:
    repo = UserRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.read(Fake().user().mail)


def test_should_persist(db_session: Any) -> None:
    repo = UserRepository(db_session)
    user = Fake().user()

    repo.create(user)
    db_user = repo.read(user.mail)

    assert db_user.mail == user.mail
    assert db_user.id == user.id


def test_should_not_create(db_session: Any) -> None:
    repo = UserRepository(db_session)

    user = Fake().user()
    repo.create(user)

    with pytest.raises(ExistsError):
        repo.create(user)
