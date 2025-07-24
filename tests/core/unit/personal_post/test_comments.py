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
from tests.fake import FakePersonalPost, FakePersonalPostComment, FakeUser


@pytest.fixture
def test_user_and_post_id(db_session: Any) -> tuple[UUID, UUID]:
    users = UserRepository(db_session)
    posts = PostRepository(db_session)

    user = FakeUser().as_user()
    created_user = users.create(user)

    post = replace(FakePersonalPost(), user_id=created_user.id).as_post()
    created_post = posts.create(post)

    return created_user.id, created_post.id


def test_should_create_comment(
    db_session: Any, test_user_and_post_id: tuple[UUID, UUID]
) -> None:
    repo = CommentRepository(db_session)
    user_id, post_id = test_user_and_post_id

    comment = replace(
        FakePersonalPostComment(), user_id=user_id, post_id=post_id
    ).as_comment()
    created = repo.create(comment)

    assert created.user_id == user_id
    assert created.post_id == post_id
    assert created.content == comment.content


def test_should_list_comments_by_post(
    db_session: Any, test_user_and_post_id: tuple[UUID, UUID]
) -> None:
    repo = CommentRepository(db_session)
    user_id, post_id = test_user_and_post_id

    for _ in range(5):
        comment = replace(
            FakePersonalPostComment(), user_id=user_id, post_id=post_id
        ).as_comment()
        repo.create(comment)

    comments = repo.get_by_post(post_id)
    assert len(comments) == 5
    assert all(c.post_id == post_id for c in comments)


def test_should_delete_comment(
    db_session: Any, test_user_and_post_id: tuple[UUID, UUID]
) -> None:
    repo = CommentRepository(db_session)
    user_id, post_id = test_user_and_post_id

    comment = replace(
        FakePersonalPostComment(), user_id=user_id, post_id=post_id
    ).as_comment()
    created = repo.create(comment)

    repo.delete(created.id)
    assert repo.get_by_post(post_id) == []


def test_should_fail_delete_unknown_comment(db_session: Any) -> None:
    repo = CommentRepository(db_session)

    with pytest.raises(DoesNotExistError):
        repo.delete(uuid4())
