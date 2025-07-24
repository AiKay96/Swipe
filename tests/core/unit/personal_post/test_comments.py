from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.core.errors import DoesNotExistError
from src.infra.repositories.personal_post.comments import (
    CommentRepository,
)
from src.infra.repositories.personal_post.posts import PostRepository
from src.infra.repositories.users import UserRepository
from tests.fake import FakePersonalPost as FakePost
from tests.fake import FakePersonalPostComment as FakeComment
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


def test_should_create_comment(db_session: Any, user_id: UUID, post_id: UUID) -> None:
    repo = CommentRepository(db_session)

    comment = replace(FakeComment(), user_id=user_id, post_id=post_id).as_comment()
    created = repo.create(comment)

    assert created.user_id == user_id
    assert created.post_id == post_id
    assert created.content == comment.content


def test_should_delete_comment(db_session: Any, user_id: UUID, post_id: UUID) -> None:
    repo = CommentRepository(db_session)

    comment = replace(FakeComment(), user_id=user_id, post_id=post_id).as_comment()
    created = repo.create(comment)

    repo.delete(created.id)
    assert repo.get(created.id) is None


def test_should_fail_delete_unknown_comment(db_session: Any) -> None:
    repo = CommentRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.delete(uuid4())
