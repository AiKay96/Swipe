from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from src.core.creator_post.posts import Post as CreatorPost
from src.core.errors import DoesNotExistError
from src.core.feed import FeedPost, Reaction
from src.infra.services.creator_post import CreatorPostService


def _make_post_with_category(user_id: UUID | None = None) -> CreatorPost:
    uid = user_id or uuid4()
    return CreatorPost(
        id=uuid4(),
        user_id=uid,
        category_id=uuid4(),
        reference_id=None,
        description="desc",
        category_tag_names=[],
        hashtag_names=[],
        media=[],
        created_at=datetime.now(),
    )


def test_should_create_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    created = _make_post_with_category()
    post_repo.create.return_value = created
    post_decorator.decorate_entity.return_value = FeedPost(
        post=created, reaction=Reaction.NONE, is_saved=False
    )

    svc = CreatorPostService(
        post_repo=post_repo,
        like_repo=like_repo,
        comment_repo=comment_repo,
        save_repo=save_repo,
        feed_pref_repo=feed_pref_repo,
        post_decorator=post_decorator,
    )

    out = svc.create_post(
        user_id=created.user_id,
        category_id=created.category_id,  # type: ignore[arg-type]
        reference_id=None,
        description=created.description,
        category_tag_names=[],
        hashtag_names=[],
        media=[],
    )

    post_repo.create.assert_called_once()
    post_decorator.decorate_entity.assert_called_once()
    _, kwargs = post_decorator.decorate_entity.call_args
    assert kwargs["is_creator"] is True
    assert out.post.id == created.id


def test_delete_post_only_by_owner() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    post_repo.get.return_value = post

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )

    svc.delete_post(post.id, post.user_id)
    post_repo.delete.assert_called_once_with(post.id)

    post_repo.delete.reset_mock()
    with pytest.raises(DoesNotExistError):
        svc.delete_post(post.id, uuid4())
    post_repo.delete.assert_not_called()


def test_like_post_new_like_updates_counts_and_points() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    post_repo.get.return_value = post
    like_repo.get.return_value = None

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )

    svc.like_post(post.user_id, post.id)

    like_repo.create.assert_called_once()
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, like_count_delta=1
    )
    feed_pref_repo.add_points.assert_called_once_with(post.user_id, post.category_id, 2)


def test_like_post_from_dislike_switches_and_points() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    existing = Mock(id=uuid4(), user_id=post.user_id, post_id=post.id, is_dislike=True)
    post_repo.get.return_value = post
    like_repo.get.return_value = existing

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )
    svc.like_post(post.user_id, post.id)

    like_repo.update.assert_called_once_with(existing.id, is_dislike=False)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, like_count_delta=1, dislike_count_delta=-1
    )
    feed_pref_repo.add_points.assert_called_once_with(post.user_id, post.category_id, 2)


def test_dislike_post_new_updates_counts_and_points() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    post_repo.get.return_value = post
    like_repo.get.return_value = None

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )
    svc.dislike_post(post.user_id, post.id)

    like_repo.create.assert_called_once()
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, dislike_count_delta=1
    )
    feed_pref_repo.add_points.assert_called_once_with(
        post.user_id, post.category_id, -2
    )


def test_dislike_post_from_like_switches_and_points() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    existing = Mock(id=uuid4(), user_id=post.user_id, post_id=post.id, is_dislike=False)
    post_repo.get.return_value = post
    like_repo.get.return_value = existing

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )
    svc.dislike_post(post.user_id, post.id)

    like_repo.update.assert_called_once_with(existing.id, is_dislike=True)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, like_count_delta=-1, dislike_count_delta=1
    )
    feed_pref_repo.add_points.assert_called_once_with(
        post.user_id, post.category_id, -2
    )


def test_unlike_post_from_like_updates_counts_and_points() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    existing = Mock(id=uuid4(), user_id=post.user_id, post_id=post.id, is_dislike=False)
    post_repo.get.return_value = post
    like_repo.get.return_value = existing

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )
    svc.unlike_post(post.user_id, post.id)

    like_repo.delete.assert_called_once_with(existing.id)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, like_count_delta=-1
    )
    feed_pref_repo.add_points.assert_called_once_with(
        post.user_id, post.category_id, -1
    )


def test_unlike_post_from_dislike_updates_counts_and_points() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    existing = Mock(id=uuid4(), user_id=post.user_id, post_id=post.id, is_dislike=True)
    post_repo.get.return_value = post
    like_repo.get.return_value = existing

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )
    svc.unlike_post(post.user_id, post.id)

    like_repo.delete.assert_called_once_with(existing.id)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, dislike_count_delta=-1
    )
    feed_pref_repo.add_points.assert_called_once_with(
        post.user_id, post.category_id, -1
    )


def test_save_and_remove_save_record_points() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    post_repo.get.return_value = post

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )

    save_repo.get.return_value = None
    svc.save_post(post.user_id, post.id)
    save_repo.create.assert_called_once()
    feed_pref_repo.add_points.assert_called_with(post.user_id, post.category_id, 5)

    feed_pref_repo.add_points.reset_mock()
    existing = Mock(id=uuid4())
    save_repo.get.return_value = existing
    svc.remove_save(post.user_id, post.id)
    save_repo.delete.assert_called_once_with(existing.id)
    feed_pref_repo.add_points.assert_called_with(post.user_id, post.category_id, -4)


def test_comment_and_remove_comment_record_points_and_checks() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    post = _make_post_with_category()
    post_repo.get.return_value = post

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )

    svc.comment_post(post.user_id, post.id, "hi")
    comment_repo.create.assert_called_once()
    feed_pref_repo.add_points.assert_called_with(post.user_id, post.category_id, 3)

    feed_pref_repo.add_points.reset_mock()
    cid = uuid4()
    comment_repo.get.return_value = Mock(id=cid, user_id=post.user_id, post_id=post.id)
    svc.remove_comment(post.id, cid, post.user_id)
    comment_repo.delete.assert_called_once_with(cid)
    feed_pref_repo.add_points.assert_called_with(post.user_id, post.category_id, -2)

    comment_repo.get.return_value = Mock(id=cid, user_id=uuid4(), post_id=post.id)
    with pytest.raises(DoesNotExistError):
        svc.remove_comment(post.id, cid, post.user_id)


def test_get_user_posts_and_saves() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    save_repo = Mock()
    feed_pref_repo = Mock()
    post_decorator = Mock()

    a = _make_post_with_category()
    b = _make_post_with_category()

    post_repo.get_posts_by_user.return_value = [a, b]
    post_repo.get_saved_posts_by_user.return_value = [b]

    post_decorator.decorate_list.side_effect = lambda **kw: [
        FeedPost(post=p, reaction=Reaction.NONE, is_saved=(p == b)) for p in kw["posts"]
    ]

    svc = CreatorPostService(
        post_repo, like_repo, comment_repo, save_repo, feed_pref_repo, post_decorator
    )

    before = datetime.now()
    posts = svc.get_user_posts(user_id=a.user_id, limit=10, before=before)
    saves = svc.get_user_saves(user_id=a.user_id, limit=10, before=before)

    post_repo.get_posts_by_user.assert_called_once_with(
        user_id=a.user_id, limit=10, before=before
    )
    post_repo.get_saved_posts_by_user.assert_called_once_with(
        user_id=a.user_id, limit=10, before=before
    )

    assert post_decorator.decorate_list.call_count == 2
    for _, kwargs in post_decorator.decorate_list.call_args_list:
        assert kwargs["is_creator"] is True

    assert [fp.post.id for fp in posts] == [a.id, b.id]
    assert [fp.post.id for fp in saves] == [b.id]
