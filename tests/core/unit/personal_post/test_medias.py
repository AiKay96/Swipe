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
def post_id(db_session: Any) -> UUID:
    user_repo = UserRepository(db_session)

    user = FakeUser().as_user()
    created_user = user_repo.create(user)

    post_repo = PostRepository(db_session)
    post = replace(FakePost(), user_id=created_user.id).as_post()
    created_post = post_repo.create(post)
    return created_post.id


def test_should_create_all_medias(db_session: Any, post_id: UUID) -> None:
    media_repo = MediaRepository(db_session)

    media_repo.create_many(
        [
            replace(FakeMedia(), post_id=post_id).as_media(),
            replace(FakeMedia(), post_id=post_id).as_media(),
        ]
    )
