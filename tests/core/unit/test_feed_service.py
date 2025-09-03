# tests/core/unit/test_feed_service.py
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

from src.core.feed import FeedPost, Reaction
from src.infra.services.cache import Cache
from src.infra.services.feed import FeedService
from tests.fake import FakeCreatorPost, FakePersonalPost


@dataclass
class FakeFeedService(FeedService):
    personal_post_repo: Any = field(default_factory=Mock)
    friend_repo: Any = field(default_factory=Mock)
    preference_repo: Any = field(default_factory=Mock)
    post_interaction_repo: Any = field(default_factory=Mock)
    follow_repo: Any = field(default_factory=Mock)
    post_repo: Any = field(default_factory=Mock)
    post_decorator: Any = field(default_factory=Mock)
    _cache: Cache = field(default_factory=Cache)


def test_should_get_feed_with_reactions() -> None:
    user_id = uuid4()
    friend_id = uuid4()
    post1 = FakePersonalPost(user_id=friend_id).as_post()
    post2 = FakePersonalPost(user_id=friend_id).as_post()

    svc = FakeFeedService()

    svc.friend_repo.get_friend_ids.return_value = [friend_id]
    svc.post_repo.get_posts_by_users.return_value = [post1, post2]

    svc.post_decorator.decorate_posts.return_value = [
        FeedPost(post=post1, reaction=Reaction.LIKE, is_saved=False),
        FeedPost(post=post2, reaction=Reaction.DISLIKE, is_saved=False),
    ]

    result = svc.get_personal_feed(user_id, before=datetime.now(), limit=10)

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

    svc = FakeFeedService()

    svc.friend_repo.get_friend_ids.return_value = [friend_id]
    svc.post_repo.get_posts_by_users.return_value = [post]
    svc.post_decorator.decorate_posts.return_value = [
        FeedPost(post=post, reaction=Reaction.NONE, is_saved=False)
    ]

    result = svc.get_personal_feed(user_id, before=datetime.now(), limit=5)

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

    svc = FakeFeedService()

    svc.post_interaction_repo.get_recent_interacted_posts.return_value = [
        interacted_post
    ]
    svc.follow_repo.get_following.return_value = [uuid4()]

    svc.post_repo.get_posts_by_users_in_category.return_value = [followed_post]
    svc.post_repo.get_trending_posts_in_category.return_value = [trending_post]

    def _decorate(posts: Sequence[Any], *args: Any, **kwargs: Any) -> list[FeedPost]:  # noqa: ARG001
        out: list[FeedPost] = []
        for p in posts:
            if p.id == followed_post.id:
                out.append(FeedPost(post=p, reaction=Reaction.LIKE, is_saved=False))
            elif p.id == trending_post.id:
                out.append(FeedPost(post=p, reaction=Reaction.DISLIKE, is_saved=True))
            elif p.id == interacted_post.id:
                out.append(FeedPost(post=p, reaction=Reaction.NONE, is_saved=False))
        return out

    svc.post_decorator.decorate_posts.side_effect = _decorate

    result = svc.get_creator_feed_by_category(
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

    for fp in result:
        if fp.post.id == followed_post.id:
            assert fp.reaction == Reaction.LIKE
            assert not fp.is_saved
        elif fp.post.id == trending_post.id:
            assert fp.reaction == Reaction.DISLIKE
            assert fp.is_saved
        elif fp.post.id == interacted_post.id:
            assert fp.reaction == Reaction.NONE
            assert not fp.is_saved


def test_normalize_weights_shift_excludes_negative() -> None:
    svc = FakeFeedService()

    a, b, c = uuid4(), uuid4(), uuid4()
    weights = [(a, 10), (b, 0), (c, -5)]

    norm = svc._normalize_weights(weights)
    m = dict(norm)

    assert m.get(c, 0.0) == 0.0
    assert abs(m[a] - (11 / 12)) < 1e-6
    assert abs(m[b] - (1 / 12)) < 1e-6


def test_get_creator_feed_negative_preferences_falls_back() -> None:
    user_id = uuid4()
    now = datetime.now()

    svc = FakeFeedService()
    svc.preference_repo.get_top_categories_with_points.return_value = [
        (uuid4(), -1),
        (uuid4(), -3),
    ]

    out = svc.get_creator_feed(
        user_id=user_id, before=now, limit=10, top_k_categories=5
    )
    assert out == []


def test_cached_follow_ids_is_reused() -> None:
    svc = FakeFeedService()
    u = uuid4()

    mock_get_following = Mock(return_value=[uuid4()])
    svc.follow_repo.get_following = mock_get_following

    a = svc._cached_follow_ids(u)
    b = svc._cached_follow_ids(u)
    assert a == b
    mock_get_following.assert_called_once()
