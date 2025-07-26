from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime, timedelta

from src.core.feed import Reaction, FeedPost
from src.infra.services.feed import FeedService
from tests.fake import FakePersonalPost


def test_should_get_feed_with_reactions() -> None:
    user_id = uuid4()
    friend_id = uuid4()
    post1 = FakePersonalPost(user_id=friend_id).as_post()
    post2 = FakePersonalPost(user_id=friend_id).as_post()

    friend_repo = Mock()
    post_repo = Mock()
    like_repo = Mock()

    friend_repo.get_friend_ids.return_value = [friend_id]
    post_repo.get_posts_by_users.return_value = [post1, post2]
    like_repo.get_user_reactions.return_value = {
        post1.id: Reaction.LIKE,
        post2.id: Reaction.DISLIKE,
    }

    service = FeedService(friend_repo, post_repo, like_repo)
    result = service.get_feed(user_id, before=datetime.now(), limit=10)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].post.id == post1.id
    assert result[0].reaction == Reaction.LIKE
    assert result[1].post.id == post2.id
    assert result[1].reaction == Reaction.DISLIKE


def test_should_return_none_reaction_if_missing() -> None:
    user_id = uuid4()
    friend_id = uuid4()
    post = FakePersonalPost(user_id=friend_id).as_post()

    friend_repo = Mock()
    post_repo = Mock()
    like_repo = Mock()

    friend_repo.get_friend_ids.return_value = [friend_id]
    post_repo.get_posts_by_users.return_value = [post]
    like_repo.get_user_reactions.return_value = {}

    service = FeedService(friend_repo, post_repo, like_repo)
    result = service.get_feed(user_id, before=datetime.now(), limit=5)

    assert len(result) == 1
    assert result[0].post.id == post.id
    assert result[0].reaction == Reaction.NONE
