from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

from src.core.feed import Reaction
from src.infra.services.feed import FeedService
from tests.fake import FakeCreatorPost, FakePersonalPost


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

    service = FeedService(
        post_repo,
        friend_repo,
        like_repo,
        Mock(),
        Mock(),
        Mock(),
        Mock(),
        Mock(),
        Mock(),
    )
    result = service.get_personal_feed(user_id, before=datetime.now(), limit=10)

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

    service = FeedService(
        post_repo,
        friend_repo,
        like_repo,
        Mock(),
        Mock(),
        Mock(),
        Mock(),
        Mock(),
        Mock(),
    )
    result = service.get_personal_feed(user_id, before=datetime.now(), limit=5)

    assert len(result) == 1
    assert result[0].post.id == post.id
    assert result[0].reaction == Reaction.NONE


def test_should_get_creator_feed_by_category() -> None:
    user_id = uuid4()
    category_id = uuid4()
    now = datetime.now()

    followed_post = FakeCreatorPost(category_id=category_id).as_post()
    trending_post = FakeCreatorPost(category_id=category_id).as_post()
    interacted_post = FakeCreatorPost(category_id=category_id).as_post()

    personal_post_repo = Mock()
    friend_repo = Mock()
    personal_post_like_repo = Mock()
    preference_repo = Mock()
    post_interaction_repo = Mock()
    follow_repo = Mock()
    post_repo = Mock()
    save_repo = Mock()
    creator_post_like_repo = Mock()

    post_interaction_repo.get_recent_interacted_posts.return_value = [interacted_post]
    follow_repo.get_following.return_value = [uuid4()]

    post_repo.get_posts_by_users_in_category.return_value = [followed_post]
    post_repo.get_trending_posts_in_category.return_value = [trending_post]

    save_repo.get_user_saves_for_posts.return_value = [trending_post.id]
    creator_post_like_repo.get_user_reactions.return_value = {
        followed_post.id: Reaction.LIKE,
        trending_post.id: Reaction.DISLIKE,
        interacted_post.id: Reaction.NONE,
    }

    service = FeedService(
        personal_post_repo,
        friend_repo,
        personal_post_like_repo,
        preference_repo,
        post_interaction_repo,
        follow_repo,
        post_repo,
        save_repo,
        creator_post_like_repo,
    )

    result = service.get_creator_feed_by_category(
        user_id=user_id,
        category_id=category_id,
        before=now,
        limit=3,
    )

    assert isinstance(result, list)
    assert len(result) == 3

    post_ids = {p.post.id for p in result}
    assert followed_post.id in post_ids
    assert trending_post.id in post_ids
    assert interacted_post.id in post_ids

    for feed_post in result:
        if feed_post.post.id == followed_post.id:
            assert feed_post.reaction == Reaction.LIKE
            assert not feed_post.is_saved
        elif feed_post.post.id == trending_post.id:
            assert feed_post.reaction == Reaction.DISLIKE
            assert feed_post.is_saved
        elif feed_post.post.id == interacted_post.id:
            assert feed_post.reaction == Reaction.NONE
            assert not feed_post.is_saved
