from typing import Any

import pytest

from src.core.errors import DoesNotExistError, ExistsError
from src.infra.repositories.users import UserRepository
from tests.fake import FakeUser


def test_should_read_user_by_id(db_session: Any) -> None:
    repo = UserRepository(db_session)
    user = FakeUser().as_user()

    repo.create(user)
    found = repo.read_by(user_id=user.id)

    assert found
    assert found.id == user.id


def test_should_read_user_by_mail(db_session: Any) -> None:
    repo = UserRepository(db_session)
    user = FakeUser().as_user()

    repo.create(user)
    found = repo.read_by(mail=user.mail)

    assert found
    assert found.mail == user.mail


def test_should_read_user_by_username(db_session: Any) -> None:
    repo = UserRepository(db_session)
    user = FakeUser().as_user()

    repo.create(user)
    found = repo.read_by(username=user.username)

    assert found
    assert found.username == user.username


def test_should_find_user_by_username(db_session: Any) -> None:
    repo = UserRepository(db_session)
    fake = FakeUser()
    user = fake.as_user()

    repo.create(user)

    created = repo.find_by_username(user.username.lower())

    assert created
    assert created.username == user.username
    assert created.mail == user.mail


def test_should_not_read_unknown_user(db_session: Any) -> None:
    repo = UserRepository(db_session)

    assert repo.read_by(user_id=FakeUser().id) is None
    assert repo.read_by(mail=FakeUser().mail) is None
    assert repo.read_by(username=FakeUser().username) is None


def test_should_persist(db_session: Any) -> None:
    repo = UserRepository(db_session)
    user = FakeUser().as_user()

    repo.create(user)
    db_user = repo.read_by(mail=user.mail)

    assert db_user
    assert db_user.mail == user.mail
    assert db_user.id == user.id


def test_should_not_create(db_session: Any) -> None:
    repo = UserRepository(db_session)

    user = FakeUser().as_user()
    repo.create(user)

    with pytest.raises(ExistsError):
        repo.create(user)


def test_should_fail_to_update_unknown_user(db_session: Any) -> None:
    repo = UserRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.update(FakeUser().id, {"display_name": FakeUser().display_name})


def test_should_update_user_fields(db_session: Any) -> None:
    repo = UserRepository(db_session)
    user = FakeUser().as_user()

    repo.create(user)

    update_user = FakeUser()
    updates = {"display_name": update_user.display_name, "bio": update_user.bio}
    repo.update(user.id, updates)

    updated = repo.read_by(user_id=user.id)
    assert updated
    assert updated.display_name == update_user.display_name
    assert updated.bio == update_user.bio
