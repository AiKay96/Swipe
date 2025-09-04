from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

from src.core.feed import FeedPost, Reaction
from src.infra.services.feed import FeedService
from tests.fake import FakeCreatorPost, FakePersonalPost


class _CacheStub:
    def __init__(self, namespace: str = "test") -> None:
        self._store: dict[str, Any] = {}
        self.namespace = namespace

    def get(self, key: str) -> Any | None:
        return self._store.get(self._k(key))

    def set(self, key: str, value: Any, ttl_sec: int) -> None:  # noqa: ARG002
        self._store[self._k(key)] = value

    def clear(self) -> None:
        self._store.clear()

    def user(self, user_id: str) -> _UserScopedCacheStub:
        return _UserScopedCacheStub(self, user_id)

    def _k(self, key: str) -> str:
        return f"{self.namespace}:{key}"


class _UserScopedCacheStub(_CacheStub):
    def __init__(self, parent: _CacheStub, user_id: str) -> None:
        self._store = parent._store
        self.namespace = parent.namespace
        self._user_prefix = f"u:{user_id}:"

    def get(self, key: str) -> Any | None:
        return super().get(self._user_prefix + key)

    def set(self, key: str, value: Any, ttl_sec: int) -> None:
        super().set(self._user_prefix + key, value, ttl_sec)


@dataclass
class FakeFeedService(FeedService):
    personal_post_repo: Any = field(default_factory=Mock)
    friend_repo: Any = field(default_factory=Mock)
    preference_repo: Any = field(default_factory=Mock)
    post_interaction_repo: Any = field(default_factory=Mock)
    follow_repo: Any = field(default_factory=Mock)
    post_repo: Any = field(default_factory=Mock)
    post_decorator: Any = field(default_factory=Mock)
    _cache: Any = field(default_factory=_CacheStub)


def test_should_get_feed_with_reactions() -> None:
    user_id = uuid4()
    friend_id = uuid4()
    post1 = FakePersonalPost(user_id=friend_id).as_post()
    post2 = FakePersonalPost(user_id=friend_id).as_post()

    svc = FakeFeedService()

    svc.friend_repo.get_friend_ids.return_value = [friend_id]
    svc.personal_post_repo.get_posts_by_users.return_value = [post1, post2]

    svc.post_decorator.decorate_list.return_value = [
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
    svc.personal_post_repo.get_posts_by_users.return_value = [post]

    svc.post_decorator.decorate_list.return_value = [
        FeedPost(post=post, reaction=Reaction.NONE, is_saved=False)
    ]

    result = svc.get_personal_feed(user_id, before=datetime.now(), limit=5)

    assert isinstance(result, list)
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

    # IMPORTANT: service calls decorate_list(user_id=..., posts=..., is_creator=True)
    def _decorate(*args: Any, **kwargs: Any) -> list[FeedPost]:
        posts: Sequence[Any] = kwargs.get("posts") or (args[1] if len(args) > 1 else [])
        out: list[FeedPost] = []
        ids = {p.id for p in posts}
        if followed_post.id in ids:
            out.append(
                FeedPost(post=followed_post, reaction=Reaction.LIKE, is_saved=False)
            )
        if trending_post.id in ids:
            out.append(
                FeedPost(post=trending_post, reaction=Reaction.DISLIKE, is_saved=True)
            )
        if interacted_post.id in ids:
            out.append(
                FeedPost(post=interacted_post, reaction=Reaction.NONE, is_saved=False)
            )
        return out

    svc.post_decorator.decorate_list.side_effect = _decorate

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

    assert abs(m[a] - (11 / 13)) < 1e-6
    assert abs(m[b] - (1 / 13)) < 1e-6
    assert abs(m[c] - (1 / 13)) < 1e-6


def test_cached_follow_ids_is_reused() -> None:
    svc = FakeFeedService()
    u = uuid4()

    mock_get_following = Mock(return_value=[uuid4()])
    svc.follow_repo.get_following = mock_get_following

    a = svc._cached_follow_ids(u)
    b = svc._cached_follow_ids(u)
    assert a == b
    mock_get_following.assert_called_once()
