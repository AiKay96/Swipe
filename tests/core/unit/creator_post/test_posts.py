from datetime import datetime
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from src.core.errors import DoesNotExistError, ForbiddenError
from src.infra.models.creator_post.category import Category
from src.infra.models.creator_post.reference import Reference
from src.infra.repositories.creator_post.categories import CategoryRepository
from src.infra.repositories.creator_post.posts import PostRepository
from src.infra.repositories.creator_post.references import ReferenceRepository
from src.infra.repositories.users import UserRepository
from tests.fake import FakeCategory, FakeCreatorPost, FakeReference, FakeUser


@pytest.fixture
def test_creator_user_id(db_session: Any) -> UUID:
    repo = UserRepository(db_session)
    user = FakeUser().as_user()
    return repo.create(user).id


@pytest.fixture
def test_category_id(db_session: Any) -> UUID:
    repo = CategoryRepository(db_session)
    fake_category = FakeCategory().as_category()
    repo.create_many([fake_category])
    inserted = db_session.query(Category).filter_by(name=fake_category.name).first()
    return cast(UUID, inserted.id)


@pytest.fixture
def test_reference_id(db_session: Any, test_category_id: UUID) -> UUID:
    repo = ReferenceRepository(db_session)
    fake_reference = FakeReference().as_reference()
    repo.create_many(test_category_id, [fake_reference])
    inserted = db_session.query(Reference).filter_by(title=fake_reference.title).first()
    return cast(UUID, inserted.id)


def test_should_create_creator_post(
    db_session: Any,
    test_creator_user_id: UUID,
    test_category_id: UUID,
    test_reference_id: UUID,
) -> None:
    repo = PostRepository(db_session)

    post = FakeCreatorPost().as_post()
    post.category_tag_names = ["Sci-fi"]
    post.user_id = test_creator_user_id
    post.category_id = test_category_id
    post.reference_id = test_reference_id
    post.hashtag_names = ["hashtag", "movie"]
    created = repo.create(post)

    assert created.user_id == post.user_id
    assert created.description == post.description
    assert created.category_tag_names == ["Sci-fi"]
    assert post.hashtag_names == ["hashtag", "movie"]


def test_should_not_create_creator_post_invalid_category_id(
    db_session: Any, test_creator_user_id: Any
) -> None:
    repo = PostRepository(db_session)
    post = FakeCreatorPost().as_post()
    post.user_id = test_creator_user_id
    post.category_id = uuid4()
    post.category_tag_names = ["Sci-fi"]

    with pytest.raises(DoesNotExistError):
        repo.create(post)


def test_should_not_create_creator_post_invalid_category_tag(
    db_session: Any, test_creator_user_id: Any, test_category_id: Any
) -> None:
    repo = PostRepository(db_session)
    post = FakeCreatorPost().as_post()
    post.user_id = test_creator_user_id
    post.category_id = test_category_id
    post.category_tag_names = ["InvalidTag"]

    with pytest.raises(ForbiddenError, match="CategoryTag.*not found"):
        repo.create(post)


def test_should_not_create_creator_post_other_categories_tag(
    db_session: Any, test_creator_user_id: Any, test_category_id: Any
) -> None:
    alt_category = FakeCategory().as_category()
    alt_category.name = "AltCat"
    alt_category.tag_names = ["OtherTag"]
    CategoryRepository(db_session).create_many([alt_category])

    post = FakeCreatorPost().as_post()
    post.user_id = test_creator_user_id
    post.category_id = test_category_id
    post.category_tag_names = ["OtherTag"]

    repo = PostRepository(db_session)
    with pytest.raises(ForbiddenError, match="CategoryTag.*not found"):
        repo.create(post)


def test_should_not_create_creator_post_invalid_reference_id(
    db_session: Any, test_creator_user_id: Any, test_category_id: Any
) -> None:
    post = FakeCreatorPost().as_post()
    post.user_id = test_creator_user_id
    post.category_id = test_category_id
    post.reference_id = uuid4()

    repo = PostRepository(db_session)
    with pytest.raises(DoesNotExistError):
        repo.create(post)


def test_get_posts_by_users(
    db_session: Any,
    test_creator_user_id: UUID,
    test_category_id: UUID,
) -> None:
    post_repo = PostRepository(db_session)

    post = FakeCreatorPost().as_post()
    post.user_id = test_creator_user_id
    post.category_id = test_category_id
    post.category_tag_names = []
    post.hashtag_names = []
    post_created = post_repo.create(post)

    posts_all = post_repo.get_posts_by_users(
        user_ids=[test_creator_user_id],
        before=datetime.now(),
        limit=10,
        category_filter=None,
    )
    assert any(p.id == post_created.id for p in posts_all)

    posts_filtered = post_repo.get_posts_by_users(
        user_ids=[test_creator_user_id],
        before=datetime.now(),
        limit=10,
        category_filter=test_category_id,
    )
    assert any(p.id == post_created.id for p in posts_filtered)


def test_should_not_get_posts_by_users_invalid_category(
    db_session: Any,
    test_creator_user_id: UUID,
    test_category_id: UUID,
) -> None:
    post_repo = PostRepository(db_session)

    post = FakeCreatorPost().as_post()
    post.user_id = test_creator_user_id
    post.category_id = test_category_id
    post.category_tag_names = []
    post.hashtag_names = []
    post_created = post_repo.create(post)

    posts_none = post_repo.get_posts_by_users(
        user_ids=[test_creator_user_id],
        before=datetime.now(),
        limit=10,
        category_filter=uuid4(),
    )
    assert not any(p.id == post_created.id for p in posts_none)
