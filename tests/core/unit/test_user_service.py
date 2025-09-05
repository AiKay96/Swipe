from unittest.mock import Mock

import pytest

from src.core.errors import DoesNotExistError, ExistsError
from src.infra.services.user import UserService
from tests.fake import FakeUser


def test_should_register_user() -> None:
    repo = Mock()
    repo.read_by.return_value = None

    service = UserService(repo)
    fake = FakeUser()
    repo.create.return_value = fake.as_user()

    user = service.register(fake.mail, fake.password)

    repo.create.assert_called_once()
    assert user.mail == fake.mail
    assert user.password == fake.password


def test_should_not_register_duplicate_user() -> None:
    repo = Mock()
    fake = FakeUser()
    repo.read_by.return_value = fake.as_user()

    service = UserService(repo)

    with pytest.raises(ExistsError):
        service.register(fake.mail, fake.password)


def test_should_get_user_by_mail() -> None:
    repo = Mock()
    fake = FakeUser()
    repo.read_by.return_value = fake.as_user()

    service = UserService(repo)

    user = service.get_by_mail(fake.mail)
    assert user.mail == fake.mail


def test_should_not_get_unknown_user_by() -> None:
    repo = Mock()
    repo.read_by.return_value = None

    service = UserService(repo)

    with pytest.raises(DoesNotExistError):
        service.get_by_mail(FakeUser().mail)


def test_should_get_user_by_username() -> None:
    repo = Mock()
    fake = FakeUser()
    repo.find_by_username.return_value = fake.as_user()

    service = UserService(repo)

    user = service.get_by_username(fake.username)
    assert user.username == fake.username


def test_should_not_get_unknown_user_by_username() -> None:
    repo = Mock()
    repo.find_by_username.return_value = None

    service = UserService(repo)

    with pytest.raises(DoesNotExistError):
        service.get_by_username(FakeUser().username)


def test_should_update_user_fields() -> None:
    repo = Mock()
    user = FakeUser()
    repo.read_by.return_value = None

    service = UserService(repo)
    update_user = FakeUser()

    service.update_user(
        user.id,
        username=update_user.username,
        display_name=update_user.display_name,
        bio=update_user.bio,
    )

    repo.update.assert_called_once_with(
        user.id,
        {
            "username": update_user.username,
            "display_name": update_user.display_name,
            "bio": update_user.bio,
        },
    )


def test_should_not_update_to_existing_username() -> None:
    repo = Mock()
    existing_user = FakeUser().as_user()
    new_user = FakeUser().as_user()

    repo.read_by.return_value = existing_user

    service = UserService(repo)

    with pytest.raises(ExistsError):
        service.update_user(new_user.id, username=existing_user.username)
