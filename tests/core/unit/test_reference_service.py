from __future__ import annotations

from io import BytesIO
from unittest.mock import Mock
from uuid import uuid4

import pandas as pd

from src.core.creator_post.categories import Category
from src.core.creator_post.references import Reference
from src.infra.services.reference import ReferenceService


def _csv_bytes(text: str) -> BytesIO:
    buf = BytesIO(text.encode("utf-8"))
    buf.seek(0)
    return buf


def test_should_create_many_categories_from_csv() -> None:
    category_repo = Mock()
    reference_repo = Mock()

    service = ReferenceService(
        category_repo=category_repo, reference_repo=reference_repo
    )

    csv = """name,tags
Movies,"Sci-fi, Drama ,  "
Books,"Fantasy, Mystery"
"""
    file = _csv_bytes(csv)

    service.create_many_categories_from_file(file, "csv")

    category_repo.create_many.assert_called_once()
    (created_categories,), _ = category_repo.create_many.call_args

    assert isinstance(created_categories, list)
    assert len(created_categories) == 2
    assert created_categories[0].name == "Movies"
    assert created_categories[0].tag_names == ["Sci-fi", "Drama"]
    assert created_categories[1].name == "Books"
    assert created_categories[1].tag_names == ["Fantasy", "Mystery"]


def test_should_create_many_references_from_csv_no_missing_values() -> None:
    category_repo = Mock()
    reference_repo = Mock()

    service = ReferenceService(
        category_repo=category_repo, reference_repo=reference_repo
    )

    category_id = uuid4()

    csv = """title,description,image_url,tags,founder,founded_year,category
Blade Runner,Neo-noir sci-fi,br.jpg,"Sci-fi,Classic",Ridley Scott,1982,Film
Her,A love story with AI,her.jpg,"Romance",Spike Jonze,2013,Film
"""
    file = _csv_bytes(csv)

    service.create_many_references_from_file(file, "csv", category_id)

    reference_repo.create_many.assert_called_once()
    (called_category_id, refs), _ = reference_repo.create_many.call_args

    assert called_category_id == category_id
    assert isinstance(refs, list)
    assert len(refs) == 2

    r1, r2 = refs[0], refs[1]
    assert isinstance(r1, Reference)
    assert isinstance(r2, Reference)

    assert r1.title == "Blade Runner"
    assert r1.description == "Neo-noir sci-fi"
    assert r1.image_url == "br.jpg"
    assert r1.tag_names == ["Sci-fi", "Classic"]
    assert r1.category_id == category_id
    assert r1.attributes == {
        "founder": "Ridley Scott",
        "founded_year": 1982,
        "category": "Film",
    }

    assert r2.title == "Her"
    assert r2.description == "A love story with AI"
    assert r2.image_url == "her.jpg"
    assert r2.tag_names == ["Romance"]
    assert r2.category_id == category_id
    assert r2.attributes == {
        "founder": "Spike Jonze",
        "founded_year": 2013,
        "category": "Film",
    }


def test_getters_delegate_to_repositories() -> None:
    category_repo = Mock()
    reference_repo = Mock()

    cats = [Category(name="Games", tag_names=["RPG"])]
    refs = [
        Reference(
            title="Dune",
            category_id=uuid4(),
            description="",
            image_url="Blank",
            tag_names=["Sci-fi"],
            attributes={},
        )
    ]
    ref_single = Reference(
        title="Solo",
        category_id=uuid4(),
        description="",
        image_url="Blank",
        tag_names=[],
        attributes={},
    )

    category_repo.get_all.return_value = cats
    reference_repo.get_by_category.return_value = refs
    reference_repo.get.return_value = ref_single

    service = ReferenceService(
        category_repo=category_repo, reference_repo=reference_repo
    )

    assert service.get_categories() == cats
    cid = uuid4()
    assert service.get_references_by_category(cid) == refs
    rid = uuid4()
    assert service.get_reference(rid) == ref_single

    category_repo.get_all.assert_called_once()
    reference_repo.get_by_category.assert_called_once_with(cid)
    reference_repo.get.assert_called_once_with(rid)


def test_should_create_many_categories_from_xlsx() -> None:
    category_repo = Mock()
    reference_repo = Mock()
    service = ReferenceService(
        category_repo=category_repo, reference_repo=reference_repo
    )

    df = pd.DataFrame(
        [
            {"name": "Music", "tags": "Rock, Jazz"},
            {"name": "Art", "tags": "Modern, Abstract"},
        ]
    )

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)

    service.create_many_categories_from_file(buf, "xlsx")

    category_repo.create_many.assert_called_once()
    (created_categories,), _ = category_repo.create_many.call_args
    assert [c.name for c in created_categories] == ["Music", "Art"]
    assert created_categories[0].tag_names == ["Rock", "Jazz"]
    assert created_categories[1].tag_names == ["Modern", "Abstract"]
