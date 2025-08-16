from dataclasses import replace
from datetime import datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

from src.core.feed import FeedPost, Reaction
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


def test_normalize_weights_shift_excludes_negative() -> None:
    svc = FeedService(
        personal_post_repo=Mock(),
        friend_repo=Mock(),
        personal_post_like_repo=Mock(),
        preference_repo=Mock(),
        post_interaction_repo=Mock(),
        follow_repo=Mock(),
        post_repo=Mock(),
        save_repo=Mock(),
        creator_post_like_repo=Mock(),
    )

    a, b, c = uuid4(), uuid4(), uuid4()
    weights = [(a, 10), (b, 0), (c, -5)]

    norm = svc._normalize_weights(weights)
    m = dict(norm)

    assert m.get(c, 0.0) == 0.0

    assert abs(m[a] - (11 / 12)) < 1e-6
    assert abs(m[b] - (1 / 12)) < 1e-6


def test_get_creator_feed_simple_mix() -> None:
    user_id = uuid4()
    now = datetime.now()

    cat_a, cat_b = uuid4(), uuid4()

    a_posts = [
        replace(FakeCreatorPost(), category_id=cat_a).as_post() for _ in range(10)
    ]
    b_posts = [
        replace(FakeCreatorPost(), category_id=cat_b).as_post() for _ in range(10)
    ]

    personal_post_repo = Mock()
    friend_repo = Mock()
    personal_post_like_repo = Mock()
    preference_repo = Mock()
    post_interaction_repo = Mock()
    follow_repo = Mock()
    post_repo = Mock()
    save_repo = Mock()
    creator_post_like_repo = Mock()

    preference_repo.get_top_categories_with_points.return_value = [
        (cat_a, 2),
        (cat_b, 1),
    ]

    def fake_cat_feed(
        *,
        user_id: UUID,  # noqa: ARG001
        category_id: UUID,
        before: datetime,  # noqa: ARG001
        limit: int,
    ) -> list[FeedPost]:
        src = a_posts if category_id == cat_a else b_posts
        chosen = src[:limit]
        return [
            FeedPost(post=p, reaction=Reaction.NONE, is_saved=False) for p in chosen
        ]

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
    # Use Mock's side_effect to replace the method
    service.get_creator_feed_by_category = Mock(side_effect=fake_cat_feed)  # type: ignore[method-assign]

    out = service.get_creator_feed(
        user_id=user_id, before=now, limit=9, top_k_categories=2
    )
    assert isinstance(out, list)
    assert len(out) == 9

    a_ids = {p.id for p in a_posts}
    b_ids = {p.id for p in b_posts}
    a_count = sum(1 for fp in out if fp.post.id in a_ids)
    b_count = sum(1 for fp in out if fp.post.id in b_ids)

    assert a_count == 6 or a_count == 5
    assert b_count == 3 or b_count == 4


def test_get_creator_feed_single_category() -> None:
    user_id = uuid4()
    now = datetime.now()
    cat = uuid4()

    posts = [replace(FakeCreatorPost(), category_id=cat).as_post() for _ in range(50)]

    service = FeedService(
        personal_post_repo=Mock(),
        friend_repo=Mock(),
        personal_post_like_repo=Mock(),
        preference_repo=Mock(),
        post_interaction_repo=Mock(),
        follow_repo=Mock(),
        post_repo=Mock(),
        save_repo=Mock(),
        creator_post_like_repo=Mock(),
    )
    service.preference_repo.get_top_categories_with_points = Mock(  # type: ignore[method-assign]
        return_value=[(cat, 10)]
    )

    def fake_cat_feed(
        *,
        user_id: UUID,  # noqa: ARG001
        category_id: UUID,  # noqa: ARG001
        before: datetime,  # noqa: ARG001
        limit: int,
    ) -> list[FeedPost]:
        chosen = posts[:limit]
        return [
            FeedPost(post=p, reaction=Reaction.NONE, is_saved=False) for p in chosen
        ]

    service.get_creator_feed_by_category = Mock(side_effect=fake_cat_feed)  # type: ignore[method-assign]

    out = service.get_creator_feed(
        user_id=user_id, before=now, limit=30, top_k_categories=1
    )
    assert len(out) == 30
    post_ids = {p.id for p in posts}
    assert all(fp.post.id in post_ids for fp in out)


def test_get_creator_feed_negative_preferences_falls_back() -> None:
    user_id = uuid4()
    now = datetime.now()

    service = FeedService(
        personal_post_repo=Mock(),
        friend_repo=Mock(),
        personal_post_like_repo=Mock(),
        preference_repo=Mock(),
        post_interaction_repo=Mock(),
        follow_repo=Mock(),
        post_repo=Mock(),
        save_repo=Mock(),
        creator_post_like_repo=Mock(),
    )

    service.preference_repo.get_top_categories_with_points = Mock(  # type: ignore[method-assign]
        return_value=[
            (uuid4(), -1),
            (uuid4(), -3),
        ]
    )

    out = service.get_creator_feed(
        user_id=user_id, before=now, limit=10, top_k_categories=5
    )
    assert out == []
