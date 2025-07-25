from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.core.errors import DoesNotExistError
from src.core.personal_post.posts import Privacy
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


def test_should_update_post_privacy(db_session: Any, test_user_id: UUID) -> None:
    repo = PostRepository(db_session)
    post = replace(FakePersonalPost(), user_id=test_user_id).as_post()

    created = repo.create(post)
    repo.update_privacy(created.id, privacy=Privacy.PUBLIC)

    updated = repo.get(created.id)
    assert updated
    assert updated.privacy == Privacy.PUBLIC


def test_should_fail_update_privacy_unknown_post(db_session: Any) -> None:
    repo = PostRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.update_privacy(uuid4(), privacy=Privacy.FRIENDS_ONLY)


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


def test_should_get_user_posts_only_public(db_session: Any, test_user_id: UUID) -> None:
    repo = PostRepository(db_session)
    post1 = replace(FakePersonalPost(), user_id=test_user_id).as_post()
    post2 = replace(FakePersonalPost(), user_id=test_user_id).as_post()

    created = repo.create(post1)
    repo.create(post2)

    repo.update_privacy(created.id, Privacy.PUBLIC)

    results = repo.get_posts_by_user(
        user_id=test_user_id,
        limit=10,
        before=datetime.utcnow(),
        include_friends_only=False,
    )

    assert len(results) == 1
    assert results[0].id == created.id


def test_should_get_user_all_posts(db_session: Any, test_user_id: UUID) -> None:
    repo = PostRepository(db_session)
    post1 = replace(FakePersonalPost(), user_id=test_user_id).as_post()
    post2 = replace(FakePersonalPost(), user_id=test_user_id).as_post()

    created1 = repo.create(post1)
    created2 = repo.create(post2)

    repo.update_privacy(created1.id, Privacy.PUBLIC)

    results = repo.get_posts_by_user(
        user_id=test_user_id,
        limit=10,
        before=datetime.utcnow(),
        include_friends_only=True,
    )

    assert len(results) == 2
    assert results[1].id == created1.id
    assert results[0].id == created2.id
