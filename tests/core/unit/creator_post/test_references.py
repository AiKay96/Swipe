from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from src.core.creator_post.references import Reference as DomainReference
from src.infra.models.creator_post.category import Category as CategoryModel
from src.infra.models.creator_post.reference import Reference as ReferenceModel
from src.infra.repositories.creator_post.categories import CategoryRepository
from src.infra.repositories.creator_post.references import ReferenceRepository
from tests.fake import FakeCategory, FakeReference


@pytest.fixture
def category_id(db_session: Any) -> UUID:
    cat_repo = CategoryRepository(db_session)

    cat = FakeCategory().as_category()
    cat.name = "Cinema"
    cat.tag_names = ["Classic", "Indie", "Sci-fi"]
    cat_repo.create_many([cat])

    inserted = db_session.query(CategoryModel).filter_by(name="Cinema").first()
    assert inserted is not None
    return cast(UUID, inserted.id)


def test_create_many_and_get_by_category_links_known_tags(
    db_session: Any, category_id: UUID
) -> None:
    ref_repo = ReferenceRepository(db_session)

    r1 = DomainReference(
        title="Metropolis",
        description="Fritz Lang classic",
        image_url="url",
        attributes={"year": 1927},
        tag_names=["Classic", "Nope"],
    )
    r2 = FakeReference().as_reference()
    r2.title = "Primer"
    r2.tag_names = ["Indie"]

    ref_repo.create_many(category_id, [r1, r2])

    domain_rows = ref_repo.get_by_category(category_id)
    titles = {r.title for r in domain_rows}
    assert {"Metropolis", "Primer"}.issubset(titles)

    d1 = next(r for r in domain_rows if r.title == "Metropolis")
    d2 = next(r for r in domain_rows if r.title == "Primer")
    assert set(d1.tag_names) == {"Classic"}
    assert set(d2.tag_names) == {"Indie"}

    db_rows = (
        db_session.query(ReferenceModel)
        .filter(ReferenceModel.category_id == category_id)
        .all()
    )
    assert len(db_rows) >= 2


def test_get_single_reference(db_session: Any, category_id: UUID) -> None:
    ref_repo = ReferenceRepository(db_session)

    ref = FakeReference().as_reference()
    ref.title = "Solaris"
    ref.tag_names = ["Sci-fi"]
    ref_repo.create_many(category_id, [ref])

    inserted = db_session.query(ReferenceModel).filter_by(title="Solaris").first()
    assert inserted is not None

    got = ref_repo.get(cast(UUID, inserted.id))
    assert got is not None
    assert got.title == "Solaris"
    assert set(got.tag_names) == {"Sci-fi"}


def test_get_by_category_empty_for_other_category(db_session: Any) -> None:
    ref_repo = ReferenceRepository(db_session)
    cat_repo = CategoryRepository(db_session)

    other = FakeCategory().as_category()
    other.name = "EmptyCat"
    other.tag_names = []
    cat_repo.create_many([other])

    other_id = db_session.query(CategoryModel).filter_by(name="EmptyCat").first()
    assert other_id is not None

    rows = ref_repo.get_by_category(cast(UUID, other_id.id))
    assert rows == []


def test_get_nonexistent_reference_returns_none(db_session: Any) -> None:
    ref_repo = ReferenceRepository(db_session)
    got = ref_repo.get(uuid4())
    assert got is None
