from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.core.errors import DoesNotExistError
from src.infra.repositories.personal_post.likes import LikeRepository
from src.infra.repositories.personal_post.posts import PostRepository
from src.infra.repositories.users import UserRepository
from tests.fake import FakePersonalPost as FakePost
from tests.fake import FakePersonalPostLike as FakeLike
from tests.fake import FakeUser


@pytest.fixture
def test_user_and_post(db_session: Any) -> tuple[UUID, UUID]:
    user_repo = UserRepository(db_session)
    post_repo = PostRepository(db_session)

    user = FakeUser().as_user()
    created_user = user_repo.create(user)

    post = replace(FakePost(), user_id=created_user.id).as_post()
    created_post = post_repo.create(post)

    return created_user.id, created_post.id


def test_should_create_like(
    db_session: Any, test_user_and_post: tuple[UUID, UUID]
) -> None:
    user_id, post_id = test_user_and_post
    repo = LikeRepository(db_session)

    like = replace(FakeLike(), user_id=user_id, post_id=post_id).as_like()
    created = repo.create(like)

    assert created.user_id == user_id
    assert created.post_id == post_id
    assert created.is_dislike is False


def test_should_get_like_by_user_and_post(
    db_session: Any, test_user_and_post: tuple[UUID, UUID]
) -> None:
    user_id, post_id = test_user_and_post
    repo = LikeRepository(db_session)

    like = replace(FakeLike(), user_id=user_id, post_id=post_id).as_like()
    repo.create(like)

    found = repo.get_by_user_and_post(user_id, post_id)

    assert found
    assert found.user_id == user_id
    assert found.post_id == post_id


def test_should_update_like(
    db_session: Any, test_user_and_post: tuple[UUID, UUID]
) -> None:
    user_id, post_id = test_user_and_post
    repo = LikeRepository(db_session)

    like = replace(FakeLike(), user_id=user_id, post_id=post_id).as_like()
    created = repo.create(like)

    repo.update(created.id, is_dislike=True)
    updated = repo.get_by_user_and_post(user_id, post_id)

    assert updated
    assert updated.is_dislike is True


def test_should_delete_like(
    db_session: Any, test_user_and_post: tuple[UUID, UUID]
) -> None:
    user_id, post_id = test_user_and_post
    repo = LikeRepository(db_session)

    like = replace(FakeLike(), user_id=user_id, post_id=post_id).as_like()
    created = repo.create(like)

    repo.delete(created.id)
    assert repo.get_by_user_and_post(user_id, post_id) is None


def test_should_fail_on_unknown_like_update(db_session: Any) -> None:
    repo = LikeRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.update(uuid4(), is_dislike=False)


def test_should_fail_on_unknown_like_delete(db_session: Any) -> None:
    repo = LikeRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.delete(uuid4())
