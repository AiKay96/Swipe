from dataclasses import replace
from typing import Any
from uuid import UUID

import pytest

from src.infra.repositories.personal_post.medias import MediaRepository
from src.infra.repositories.personal_post.posts import PostRepository
from src.infra.repositories.users import UserRepository
from tests.fake import (
    FakePersonalPost as FakePost,
)
from tests.fake import (
    FakePersonalPostMedia as FakeMedia,
)
from tests.fake import (
    FakeUser,
)


@pytest.fixture
def test_user_and_post(db_session: Any) -> tuple[UUID, UUID]:
    user_repo = UserRepository(db_session)
    post_repo = PostRepository(db_session)

    user = FakeUser().as_user()
    created_user = user_repo.create(user)

    post = replace(FakePost(), user_id=created_user.id).as_post()
    created_post = post_repo.create(post)

    return created_user.id, created_post.id


def test_should_create_media(
    db_session: Any, test_user_and_post: tuple[UUID, UUID]
) -> None:
    _, post_id = test_user_and_post
    repo = MediaRepository(db_session)

    media = replace(FakeMedia(), post_id=post_id).as_media()
    created = repo.create(media)

    assert created.post_id == post_id
    assert created.url == media.url
    assert created.media_type == media.media_type


def test_should_list_media_by_post(
    db_session: Any, test_user_and_post: tuple[UUID, UUID]
) -> None:
    _, post_id = test_user_and_post
    repo = MediaRepository(db_session)

    for _ in range(3):
        media = replace(FakeMedia(), post_id=post_id).as_media()
        repo.create(media)

    results = repo.list_by_post(post_id)

    assert len(results) == 3
    assert all(m.post_id == post_id for m in results)
