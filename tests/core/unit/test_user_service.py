from unittest.mock import Mock

import pytest

from src.core.errors import DoesNotExistError, ExistsError
from src.infra.services.user import UserService
from tests.fake import FakeUser


def test_should_register_user() -> None:
    repo = Mock()
    repo.read_by_mail.return_value = None
    repo.read_by_username.return_value = None

    service = UserService(repo)
    fake = FakeUser()

    user = service.register(fake.mail, fake.password)

    repo.create.assert_called_once()
    assert user.mail == fake.mail
    assert user.password == fake.password
    assert user.username == user.display_name
    assert isinstance(user.username, str)


def test_should_not_register_duplicate_user() -> None:
    repo = Mock()
    fake = FakeUser()
    repo.read_by_mail.return_value = fake.as_user()

    service = UserService(repo)

    with pytest.raises(ExistsError):
        service.register(fake.mail, fake.password)


def test_should_get_user_by_mail() -> None:
    repo = Mock()
    fake = FakeUser()
    repo.read_by_mail.return_value = fake.as_user()

    service = UserService(repo)

    user = service.get_by_mail(fake.mail)
    assert user.mail == fake.mail


def test_should_not_get_unknown_user_by_mail() -> None:
    repo = Mock()
    repo.read_by_mail.return_value = None

    service = UserService(repo)

    with pytest.raises(DoesNotExistError):
        service.get_by_mail(FakeUser().mail)
