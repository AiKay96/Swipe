from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.core.errors import DoesNotExistError
from src.infra.services.personal_post import PersonalPostService
from tests.fake import (
    FakePersonalPost,
    FakePersonalPostComment,
    FakePersonalPostLike,
    FakePersonalPostMedia,
)


def test_should_create_post_with_media() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    post = FakePersonalPost().as_post()
    media = [FakePersonalPostMedia().as_media()]
    post_repo.create.return_value = post

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    result = service.create_post(post.user_id, post.description, media)

    media_repo.create_many.assert_called_once_with(media)
    post_repo.create.assert_called_once()
    assert result.description == post.description


def test_should_delete_own_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    service.delete_post(post.id, post.user_id)

    post_repo.delete.assert_called_once_with(post.id)


def test_should_fail_deleting_others_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)

    with pytest.raises(DoesNotExistError):
        service.delete_post(post.id, uuid4())


def test_should_like_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post
    like_repo.get.return_value = None

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    service.like_post(post.user_id, post.id)

    like_repo.create.assert_called_once()
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, like_count_delta=1
    )


def test_should_switch_dislike_to_like() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    post = FakePersonalPost().as_post()
    like = FakePersonalPostLike(is_dislike=True).as_like()
    post_repo.get.return_value = post
    like_repo.get.return_value = like

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    service.like_post(like.user_id, like.post_id)

    like_repo.update.assert_called_once_with(like.id, is_dislike=False)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=like.post_id, like_count_delta=1, dislike_count_delta=-1
    )


def test_should_dislike_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    post = FakePersonalPost().as_post()
    post_repo.get.return_value = post
    like_repo.get.return_value = None

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    service.dislike_post(post.user_id, post.id)

    like_repo.create.assert_called_once()
    post_repo.update_like_counts.assert_called_once_with(
        post_id=post.id, dislike_count_delta=1
    )


def test_should_switch_like_to_dislike() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    post = FakePersonalPost().as_post()
    like = FakePersonalPostLike(is_dislike=False).as_like()
    post_repo.get.return_value = post
    like_repo.get.return_value = like

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    service.dislike_post(like.user_id, like.post_id)

    like_repo.update.assert_called_once_with(like.id, is_dislike=True)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=like.post_id, like_count_delta=-1, dislike_count_delta=1
    )


def test_should_unlike_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    post = FakePersonalPost().as_post()
    like = FakePersonalPostLike(is_dislike=False).as_like()
    post_repo.get.return_value = post
    like_repo.get.return_value = like

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    service.unlike_post(like.user_id, like.post_id)

    like_repo.delete.assert_called_once_with(like.id)
    post_repo.update_like_counts.assert_called_once_with(
        post_id=like.post_id, like_count_delta=-1
    )


def test_should_comment_post() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    comment = FakePersonalPostComment().as_comment()
    comment_repo.create.return_value = comment

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    result = service.comment_post(comment.user_id, comment.post_id, comment.content)

    comment_repo.create.assert_called_once()
    assert result.content == comment.content


def test_should_remove_own_comment() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    comment = FakePersonalPostComment().as_comment()
    comment_repo.get.return_value = comment

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)
    service.remove_comment(comment.id, comment.user_id)

    comment_repo.delete.assert_called_once_with(comment.id)


def test_should_fail_removing_others_comment() -> None:
    post_repo = Mock()
    like_repo = Mock()
    comment_repo = Mock()
    media_repo = Mock()

    comment = FakePersonalPostComment().as_comment()
    comment_repo.get.return_value = comment

    service = PersonalPostService(post_repo, like_repo, comment_repo, media_repo)

    with pytest.raises(DoesNotExistError):
        service.remove_comment(comment.id, uuid4())
