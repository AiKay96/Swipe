from typing import Any

from src.infra.models.creator_post.category import Category as CategoryModel
from src.infra.models.creator_post.category_tag import CategoryTag as CategoryTagModel
from src.infra.repositories.creator_post.categories import CategoryRepository
from tests.fake import FakeCategory


def test_should_create_categories_and_tags(db_session: Any) -> None:
    repo = CategoryRepository(db_session)

    cat1 = FakeCategory().as_category()
    cat1.name = "Movies"
    cat1.tag_names = ["Sci-fi", "Drama"]

    cat2 = FakeCategory().as_category()
    cat2.name = "Books"
    cat2.tag_names = ["Fantasy", "Mystery"]

    repo.create_many([cat1, cat2])

    rows = db_session.query(CategoryModel).all()
    names = {r.name for r in rows}
    assert {"Movies", "Books"}.issubset(names)

    movies = db_session.query(CategoryModel).filter_by(name="Movies").first()
    books = db_session.query(CategoryModel).filter_by(name="Books").first()
    assert movies is not None
    assert books is not None

    movie_tags = {
        t.name
        for t in db_session.query(CategoryTagModel)
        .filter_by(category_id=movies.id)
        .all()
    }
    book_tags = {
        t.name
        for t in db_session.query(CategoryTagModel)
        .filter_by(category_id=books.id)
        .all()
    }

    assert movie_tags == {"Sci-fi", "Drama"}
    assert book_tags == {"Fantasy", "Mystery"}


def test_get_all_names_returns_mapping(db_session: Any) -> None:
    repo = CategoryRepository(db_session)

    cat = FakeCategory().as_category()
    cat.name = "Gaming"
    cat.tag_names = ["RPG", "Action"]
    repo.create_many([cat])

    mapping = repo.get_all_names()
    assert isinstance(mapping, dict)

    found = [cid for cid, name in mapping.items() if name == "Gaming"]
    assert len(found) == 1


def test_get_all_returns_domain_objects_with_tags(db_session: Any) -> None:
    repo = CategoryRepository(db_session)

    cat = FakeCategory().as_category()
    cat.name = "Music"
    cat.tag_names = ["Rock", "Jazz"]
    repo.create_many([cat])

    domain_rows = repo.get_all()
    d = next((c for c in domain_rows if c.name == "Music"), None)
    assert d is not None
    assert set(d.tag_names) == {"Rock", "Jazz"}
