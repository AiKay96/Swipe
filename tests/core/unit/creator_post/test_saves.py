from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.core.errors import DoesNotExistError
from src.infra.repositories.creator_post.posts import PostRepository
from src.infra.repositories.creator_post.saves import SaveRepository
from src.infra.repositories.users import UserRepository
from tests.fake import FakeCreatorPost as FakePost
from tests.fake import FakeSave as FakeSave
from tests.fake import FakeUser


@pytest.fixture
def creator_user_id(db_session: Any) -> UUID:
    user_repo = UserRepository(db_session)
    user = FakeUser().as_user()
    return user_repo.create(user).id


@pytest.fixture
def creator_post_id(db_session: Any, creator_user_id: UUID) -> UUID:
    post_repo = PostRepository(db_session)
    post = replace(FakePost(), user_id=creator_user_id).as_post()
    return post_repo.create(post).id


def test_should_create_save(
    db_session: Any, creator_user_id: UUID, creator_post_id: UUID
) -> None:
    repo = SaveRepository(db_session)
    save = replace(
        FakeSave(), user_id=creator_user_id, post_id=creator_post_id
    ).as_save()
    created = repo.create(save)

    assert created.user_id == creator_user_id
    assert created.post_id == creator_post_id


def test_should_get_save(
    db_session: Any, creator_user_id: UUID, creator_post_id: UUID
) -> None:
    repo = SaveRepository(db_session)
    save = replace(
        FakeSave(), user_id=creator_user_id, post_id=creator_post_id
    ).as_save()
    repo.create(save)

    found = repo.get(creator_user_id, creator_post_id)
    assert found is not None
    assert found.user_id == creator_user_id
    assert found.post_id == creator_post_id


def test_should_delete_save(
    db_session: Any, creator_user_id: UUID, creator_post_id: UUID
) -> None:
    repo = SaveRepository(db_session)
    save = replace(
        FakeSave(), user_id=creator_user_id, post_id=creator_post_id
    ).as_save()
    created = repo.create(save)

    repo.delete(created.id)
    assert repo.get(creator_user_id, creator_post_id) is None


def test_should_fail_on_unknown_save_delete(db_session: Any) -> None:
    repo = SaveRepository(db_session)
    with pytest.raises(DoesNotExistError):
        repo.delete(uuid4())


def test_should_get_user_saves_for_posts(
    db_session: Any, creator_user_id: UUID
) -> None:
    post_repo = PostRepository(db_session)
    save_repo = SaveRepository(db_session)

    post1 = post_repo.create(replace(FakePost(), user_id=creator_user_id).as_post())
    post2 = post_repo.create(replace(FakePost(), user_id=creator_user_id).as_post())
    post3 = post_repo.create(replace(FakePost(), user_id=creator_user_id).as_post())

    save_repo.create(
        replace(FakeSave(), user_id=creator_user_id, post_id=post1.id).as_save()
    )
    save_repo.create(
        replace(FakeSave(), user_id=creator_user_id, post_id=post2.id).as_save()
    )

    saved_post_ids = save_repo.get_user_saves_for_posts(
        user_id=creator_user_id, post_ids=[post1.id, post2.id, post3.id]
    )

    assert post1.id in saved_post_ids
    assert post2.id in saved_post_ids
    assert post3.id not in saved_post_ids
