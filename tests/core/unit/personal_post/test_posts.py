from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.core.errors import DoesNotExistError
from src.infra.repositories.personal_post.posts import PostRepository
from src.infra.repositories.users import UserRepository
from tests.fake import FakePersonalPost, FakeUser


@pytest.fixture
def test_user_id(db_session: Any) -> UUID:
    repo = UserRepository(db_session)
    user = FakeUser().as_user()

    created = repo.create(user)
    return created.id


def test_should_create_post(db_session: Any, test_user_id: UUID) -> None:
    repo = PostRepository(db_session)
    post = replace(FakePersonalPost(), user_id=test_user_id).as_post()

    created = repo.create(post)

    assert created.user_id == post.user_id


def test_should_get_post_by_id(db_session: Any, test_user_id: UUID) -> None:
    repo = PostRepository(db_session)
    post = replace(FakePersonalPost(), user_id=test_user_id).as_post()

    created = repo.create(post)
    fetched = repo.get(created.id)

    assert fetched
    assert fetched.id == created.id


def test_should_update_like_counts(db_session: Any, test_user_id: UUID) -> None:
    repo = PostRepository(db_session)
    post = replace(FakePersonalPost(), user_id=test_user_id).as_post()

    created = repo.create(post)
    repo.update_like_counts(created.id, like_count_delta=10, dislike_count_delta=2)

    updated = repo.get(created.id)
    assert updated
    assert updated.like_count == 10
    assert updated.dislike_count == 2


def test_should_delete_post(db_session: Any, test_user_id: UUID) -> None:
    repo = PostRepository(db_session)
    post = replace(FakePersonalPost(), user_id=test_user_id).as_post()

    created = repo.create(post)
    repo.delete(created.id)

    assert repo.get(created.id) is None


def test_should_fail_delete_unknown(db_session: Any) -> None:
    repo = PostRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.delete(uuid4())
