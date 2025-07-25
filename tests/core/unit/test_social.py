from typing import Any

from src.infra.repositories.social import FollowRepository, FriendRepository
from src.infra.repositories.users import UserRepository
from tests.fake import FakeUser


def test_should_follow_and_unfollow_user(db_session: Any) -> None:
    user_repo = UserRepository(db_session)
    follower = user_repo.create(FakeUser().as_user())
    following = user_repo.create(FakeUser().as_user())

    repo = FollowRepository(db_session)

    repo.follow(follower.id, following.id)
    assert repo.get(follower.id, following.id)

    repo.unfollow(follower.id, following.id)
    assert repo.get(follower.id, following.id) is None


def test_should_send_and_delete_friend_request(db_session: Any) -> None:
    user_repo = UserRepository(db_session)
    sender = user_repo.create(FakeUser().as_user())
    receiver = user_repo.create(FakeUser().as_user())

    repo = FriendRepository(db_session)

    repo.send_request(sender.id, receiver.id)
    assert repo.get_request(sender.id, receiver.id)

    repo.delete_request(sender.id, receiver.id)
    assert repo.get_request(sender.id, receiver.id) is None


def test_should_accept_friend_request(db_session: Any) -> None:
    user_repo = UserRepository(db_session)
    sender = user_repo.create(FakeUser().as_user())
    receiver = user_repo.create(FakeUser().as_user())

    repo = FriendRepository(db_session)

    repo.send_request(sender.id, receiver.id)
    repo.accept_request(sender.id, receiver.id)

    assert repo.get_request(sender.id, receiver.id) is None
    assert repo.get_friend(sender.id, receiver.id)
    assert repo.get_friend(receiver.id, sender.id)


def test_should_return_followers_and_following(db_session: Any) -> None:
    user_repo = UserRepository(db_session)
    user = user_repo.create(FakeUser().as_user())
    follower = user_repo.create(FakeUser().as_user())
    following = user_repo.create(FakeUser().as_user())

    repo = FollowRepository(db_session)

    repo.follow(follower.id, user.id)
    repo.follow(user.id, following.id)

    followers = repo.get_followers(user.id)
    following_list = repo.get_following(user.id)

    assert follower.id in followers
    assert following.id in following_list


def test_should_return_friends_of_user(db_session: Any) -> None:
    user_repo = UserRepository(db_session)
    user1 = user_repo.create(FakeUser().as_user())
    user2 = user_repo.create(FakeUser().as_user())

    repo = FriendRepository(db_session)

    repo.send_request(user1.id, user2.id)
    repo.accept_request(user1.id, user2.id)

    friends1 = repo.get_friends(user1.id)
    friends2 = repo.get_friends(user2.id)

    assert user2.id in friends1
    assert user1.id in friends2


def test_should_return_incoming_friend_requests(db_session: Any) -> None:
    user_repo = UserRepository(db_session)
    sender = user_repo.create(FakeUser().as_user())
    receiver = user_repo.create(FakeUser().as_user())

    repo = FriendRepository(db_session)

    repo.send_request(sender.id, receiver.id)
    requests = repo.get_requests_to(receiver.id)

    assert sender.id in requests
