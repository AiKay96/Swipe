from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.core.errors import DoesNotExistError, ExistsError, ForbiddenError
from src.core.social import FriendStatus
from src.infra.services.social import SocialService
from tests.fake import FakeUser


def test_should_follow_user() -> None:
    follow_repo = Mock()
    friend_repo = Mock()
    user_repo = Mock()

    user = FakeUser().as_user()
    target = FakeUser().as_user()

    user_repo.read_by.side_effect = (
        lambda user_id=None: target if user_id == target.id else None
    )
    follow_repo.get.return_value = None

    service = SocialService(follow_repo, friend_repo, user_repo)
    service.follow(user.id, target.id)

    follow_repo.follow.assert_called_once_with(user.id, target.id)


def test_should_fail_follow_self() -> None:
    service = SocialService(Mock(), Mock(), Mock())
    user = FakeUser().as_user()

    with pytest.raises(ForbiddenError):
        service.follow(user.id, user.id)


def test_should_fail_follow_if_user_not_found() -> None:
    follow_repo = Mock()
    user_repo = Mock()
    user_repo.read_by.return_value = None

    service = SocialService(follow_repo, Mock(), user_repo)

    with pytest.raises(DoesNotExistError):
        service.follow(uuid4(), uuid4())


def test_should_fail_follow_if_already_following() -> None:
    follow_repo = Mock()
    friend_repo = Mock()
    user_repo = Mock()

    user = FakeUser().as_user()
    target = FakeUser().as_user()

    user_repo.read_by.return_value = target
    follow_repo.get.return_value = True

    service = SocialService(follow_repo, friend_repo, user_repo)

    with pytest.raises(ExistsError):
        service.follow(user.id, target.id)


def test_should_send_friend_request() -> None:
    follow_repo = Mock()
    friend_repo = Mock()
    user_repo = Mock()

    sender = FakeUser().as_user()
    receiver = FakeUser().as_user()

    user_repo.read_by.return_value = receiver
    friend_repo.get_friend.return_value = None
    friend_repo.get_request.return_value = None

    service = SocialService(follow_repo, friend_repo, user_repo)
    service.send_friend_request(sender.id, receiver.id)

    friend_repo.send_request.assert_called_once_with(sender.id, receiver.id)


def test_should_fail_send_friend_request_to_self() -> None:
    service = SocialService(Mock(), Mock(), Mock())
    user = FakeUser().as_user()

    with pytest.raises(ForbiddenError):
        service.send_friend_request(user.id, user.id)


def test_should_fail_send_friend_request_if_user_not_found() -> None:
    user = FakeUser().as_user()
    user_repo = Mock()
    user_repo.read_by.return_value = None

    service = SocialService(Mock(), Mock(), user_repo)

    with pytest.raises(DoesNotExistError):
        service.send_friend_request(user.id, uuid4())


def test_should_fail_send_friend_request_if_already_friends() -> None:
    sender = FakeUser().as_user()
    receiver = FakeUser().as_user()

    friend_repo = Mock()
    friend_repo.get_friend.return_value = True
    user_repo = Mock()
    user_repo.read_by.return_value = receiver

    service = SocialService(Mock(), friend_repo, user_repo)

    with pytest.raises(ExistsError):
        service.send_friend_request(sender.id, receiver.id)


def test_should_fail_send_friend_request_if_already_requested() -> None:
    sender = FakeUser().as_user()
    receiver = FakeUser().as_user()

    friend_repo = Mock()
    friend_repo.get_friend.return_value = None
    friend_repo.get_request.return_value = True
    user_repo = Mock()
    user_repo.read_by.return_value = receiver

    service = SocialService(Mock(), friend_repo, user_repo)

    with pytest.raises(ExistsError):
        service.send_friend_request(sender.id, receiver.id)


def test_should_accept_friend_request() -> None:
    sender = FakeUser().as_user()
    receiver = FakeUser().as_user()

    friend_repo = Mock()
    friend_repo.get_friend.return_value = None
    friend_repo.get_request.return_value = True
    user_repo = Mock()
    user_repo.read_by.return_value = sender

    service = SocialService(Mock(), friend_repo, user_repo)
    service.accept_friend_request(sender.id, receiver.id)

    friend_repo.accept_request.assert_called_once_with(sender.id, receiver.id)


def test_should_fail_accept_own_friend_request() -> None:
    user = FakeUser().as_user()
    service = SocialService(Mock(), Mock(), Mock())

    with pytest.raises(ForbiddenError):
        service.accept_friend_request(user.id, user.id)


def test_should_fail_accept_if_user_missing() -> None:
    user_repo = Mock()
    user_repo.read_by.return_value = None

    service = SocialService(Mock(), Mock(), user_repo)

    with pytest.raises(DoesNotExistError):
        service.accept_friend_request(uuid4(), uuid4())


def test_should_fail_accept_if_already_friends() -> None:
    sender = FakeUser().as_user()
    receiver = FakeUser().as_user()

    friend_repo = Mock()
    friend_repo.get_friend.return_value = True
    user_repo = Mock()
    user_repo.read_by.return_value = sender

    service = SocialService(Mock(), friend_repo, user_repo)

    with pytest.raises(ExistsError):
        service.accept_friend_request(sender.id, receiver.id)


def test_should_fail_accept_if_request_missing() -> None:
    sender = FakeUser().as_user()
    receiver = FakeUser().as_user()

    friend_repo = Mock()
    friend_repo.get_friend.return_value = None
    friend_repo.get_request.return_value = None
    user_repo = Mock()
    user_repo.read_by.return_value = sender

    service = SocialService(Mock(), friend_repo, user_repo)

    with pytest.raises(DoesNotExistError):
        service.accept_friend_request(sender.id, receiver.id)


def test_should_get_friend_status_all_cases() -> None:
    user = FakeUser().as_user()
    other = FakeUser().as_user()

    friend_repo = Mock()
    follow_repo = Mock()
    user_repo = Mock()
    user_repo.read_by.return_value = other

    service = SocialService(follow_repo, friend_repo, user_repo)

    friend_repo.get_friend.return_value = True
    assert service.get_friend_status(user.id, other.id) == FriendStatus.FRIENDS

    friend_repo.get_friend.return_value = None
    friend_repo.get_request.side_effect = (
        lambda u1, u2: True if (u1 == user.id and u2 == other.id) else None
    )
    assert service.get_friend_status(user.id, other.id) == FriendStatus.PENDING_OUTGOING

    friend_repo.get_request.side_effect = (
        lambda u1, u2: True if (u1 == other.id and u2 == user.id) else None
    )
    assert service.get_friend_status(user.id, other.id) == FriendStatus.PENDING_INCOMING

    friend_repo.get_request.side_effect = lambda *_: None
    assert service.get_friend_status(user.id, other.id) == FriendStatus.NOT_FRIENDS


def test_should_fail_friend_status_if_user_missing() -> None:
    user = FakeUser().as_user()
    user_repo = Mock()
    user_repo.read_by.return_value = None

    service = SocialService(Mock(), Mock(), user_repo)
    with pytest.raises(DoesNotExistError):
        service.get_friend_status(user.id, uuid4())


def test_should_get_follow_status() -> None:
    user = FakeUser().as_user()
    other = FakeUser().as_user()

    follow_repo = Mock()
    follow_repo.get.return_value = True
    user_repo = Mock()
    user_repo.read_by.return_value = other

    service = SocialService(follow_repo, Mock(), user_repo)
    assert service.is_following(user.id, other.id) is True

    follow_repo.get.return_value = None
    assert service.is_following(user.id, other.id) is False


def test_should_fail_follow_status_if_user_missing() -> None:
    user = FakeUser().as_user()
    user_repo = Mock()
    user_repo.read_by.return_value = None

    service = SocialService(Mock(), Mock(), user_repo)
    with pytest.raises(DoesNotExistError):
        service.is_following(user.id, uuid4())
