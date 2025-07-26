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
def user_id(db_session: Any) -> UUID:
    user_repo = UserRepository(db_session)

    user = FakeUser().as_user()
    created = user_repo.create(user)

    return created.id


@pytest.fixture
def post_id(db_session: Any, user_id: UUID) -> UUID:
    post_repo = PostRepository(db_session)
    post = replace(FakePost(), user_id=user_id).as_post()
    created = post_repo.create(post)
    return created.id


def test_should_create_like(db_session: Any, user_id: UUID, post_id: UUID) -> None:
    repo = LikeRepository(db_session)

    like = replace(FakeLike(), user_id=user_id, post_id=post_id).as_like()
    created = repo.create(like)

    assert created.user_id == user_id
    assert created.post_id == post_id
    assert created.is_dislike is False


def test_should_get_like(db_session: Any, user_id: UUID, post_id: UUID) -> None:
    repo = LikeRepository(db_session)

    like = replace(FakeLike(), user_id=user_id, post_id=post_id).as_like()
    repo.create(like)

    found = repo.get(user_id, post_id)

    assert found
    assert found.user_id == user_id
    assert found.post_id == post_id


def test_should_update_like(db_session: Any, user_id: UUID, post_id: UUID) -> None:
    repo = LikeRepository(db_session)

    like = replace(FakeLike(), user_id=user_id, post_id=post_id).as_like()
    created = repo.create(like)

    repo.update(created.id, is_dislike=True)
    updated = repo.get(user_id, post_id)

    assert updated
    assert updated.is_dislike is True


def test_should_delete_like(db_session: Any, user_id: UUID, post_id: UUID) -> None:
    repo = LikeRepository(db_session)

    like = replace(FakeLike(), user_id=user_id, post_id=post_id).as_like()
    created = repo.create(like)

    repo.delete(created.id)
    assert repo.get(user_id, post_id) is None


def test_should_fail_on_unknown_like_update(db_session: Any) -> None:
    repo = LikeRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.update(uuid4(), is_dislike=False)


def test_should_fail_on_unknown_like_delete(db_session: Any) -> None:
    repo = LikeRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.delete(uuid4())


def test_should_get_user_reactions(db_session: Any, user_id: UUID) -> None:
    post_repo = PostRepository(db_session)
    like_repo = LikeRepository(db_session)

    post1 = post_repo.create(replace(FakePost(), user_id=user_id).as_post())
    post2 = post_repo.create(replace(FakePost(), user_id=user_id).as_post())
    post3 = post_repo.create(replace(FakePost(), user_id=user_id).as_post())

    like_repo.create(replace(FakeLike(), user_id=user_id, post_id=post1.id).as_like())
    like_repo.create(
        replace(FakeLike(is_dislike=True), user_id=user_id, post_id=post2.id).as_like()
    )

    reactions = like_repo.get_user_reactions(user_id, [post1.id, post2.id, post3.id])

    assert reactions[post1.id].value == "like"
    assert reactions[post2.id].value == "dislike"
    assert post3.id not in reactions
