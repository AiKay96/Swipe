from dataclasses import replace
from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.core.errors import DoesNotExistError
from src.core.feed import FeedPost, Reaction
from src.core.personal_post.posts import Post, Privacy
from src.infra.services.personal_post import PersonalPostService
from tests.fake import (
    FakePersonalPost,
    FakePersonalPostComment,
    FakePersonalPostLike,
)


def test_should_create_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()
    post_decorator = Mock()

    post = FakePersonalPost().as_post()
    post_repo.create.return_value = post

    post_decorator.decorate_entity.return_value = FeedPost(
        post=post, reaction=Reaction.NONE, is_saved=None
    )

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, post_decorator
    )
    result = service.create_post(post.user_id, post.description, [])

    post_repo.create.assert_called_once()
    assert result.post.description == post.description


def test_should_delete_own_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.delete_post(post.id, post.user_id)

    post_repo.delete.assert_called_once_with(post.id)


def test_should_fail_deleting_others_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )

    with pytest.raises(DoesNotExistError):
        service.delete_post(post.id, uuid4())


def test_should_like_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post
    like_repo.get.return_value = None

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.like_post(post.user_id, post.id)

    like_repo.create.assert_called_once()
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, like_count_delta=1
    )


def test_should_switch_dislike_to_like() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    like = FakePersonalPostLike(is_dislike=True).as_like()
    post_repo.get.return_value = post
    like_repo.get.return_value = like

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.like_post(like.user_id, like.post_id)

    like_repo.update.assert_called_once_with(like.id, is_dislike=False)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=like.post_id, like_count_delta=1, dislike_count_delta=-1
    )


def test_should_dislike_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post
    like_repo.get.return_value = None

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.dislike_post(post.user_id, post.id)

    like_repo.create.assert_called_once()
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, dislike_count_delta=1
    )


def test_should_switch_like_to_dislike() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    like = FakePersonalPostLike(is_dislike=False).as_like()
    post_repo.get.return_value = post
    like_repo.get.return_value = like

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.dislike_post(like.user_id, like.post_id)

    like_repo.update.assert_called_once_with(like.id, is_dislike=True)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=like.post_id, like_count_delta=-1, dislike_count_delta=1
    )


def test_should_unlike_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    like = FakePersonalPostLike(is_dislike=False).as_like()
    post_repo.get.return_value = post
    like_repo.get.return_value = like

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.unlike_post(like.user_id, like.post_id)

    like_repo.delete.assert_called_once_with(like.id)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=like.post_id, like_count_delta=-1
    )


def test_should_toggle_privacy_from_public_to_friends() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    post = replace(post, privacy=Privacy.PUBLIC)
    post_repo.get.return_value = post

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.change_privacy(post.user_id, post.id)

    post_repo.update_privacy.assert_called_once_with(post.id, Privacy.FRIENDS_ONLY)


def test_should_toggle_privacy_from_friends_to_public() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.change_privacy(post.user_id, post.id)

    post_repo.update_privacy.assert_called_once_with(post.id, Privacy.PUBLIC)


def test_should_comment_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    comment = FakePersonalPostComment().as_comment()
    comment_repo.create.return_value = comment

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.comment_post(comment.user_id, comment.post_id, comment.content)

    comment_repo.create.assert_called_once()


def test_should_remove_own_comment() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    comment = FakePersonalPostComment().as_comment()
    comment_repo.get.return_value = comment

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )
    service.remove_comment(comment.post_id, comment.id, comment.user_id)

    comment_repo.delete.assert_called_once_with(comment.id)


def test_should_fail_removing_others_comment() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()

    comment = FakePersonalPostComment().as_comment()
    comment_repo.get.return_value = comment

    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, Mock()
    )

    with pytest.raises(DoesNotExistError):
        service.remove_comment(comment.post_id, comment.id, uuid4())


def test_should_get_user_posts() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    friend_repo = Mock()
    post_decorator = Mock()

    public_post = replace(FakePersonalPost(), privacy=Privacy.PUBLIC).as_post()
    friends_post = FakePersonalPost().as_post()
    from_user_id = uuid4()

    friend_repo.get_friend.return_value = True
    post_repo.get_posts_by_user.return_value = [public_post, friends_post]

    post_decorator.decorate_list.return_value = [
        FeedPost(post=public_post, reaction=Reaction.NONE, is_saved=None),
        FeedPost(post=friends_post, reaction=Reaction.NONE, is_saved=None),
    ]

    now = datetime.now()
    service = PersonalPostService(
        post_repo, like_repo, comment_repo, friend_repo, post_decorator
    )
    results = service.get_user_posts(
        user_id=public_post.user_id,
        from_user_id=from_user_id,
        before=now,
        limit=10,
    )

    friend_repo.get_friend.assert_called_once_with(public_post.user_id, from_user_id)
    post_repo.get_posts_by_user.assert_called_once_with(
        user_id=public_post.user_id,
        limit=10,
        before=now,
        include_friends_only=True,
    )

    assert len(results) == 2
    privacies: set[Privacy] = set()
    for fp in results:
        assert isinstance(fp.post, Post)
        privacies.add(fp.post.privacy)
    assert privacies == {Privacy.PUBLIC, Privacy.FRIENDS_ONLY}
