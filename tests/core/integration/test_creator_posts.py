from dataclasses import replace
from datetime import datetime
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.infra.models.creator_post.category import Category
from src.infra.repositories.creator_post.categories import CategoryRepository
from tests.fake import FakeCategory, FakeCreatorPost, FakeUser


@pytest.fixture
def user(client: TestClient) -> FakeUser:
    user = FakeUser()
    response = client.post("/users", json=user.as_create_dict())
    assert response.status_code == 201
    username = response.json()["user"]["username"]
    return replace(user, id=response.json()["user"]["id"], username=username)


@pytest.fixture
def test_client(client: TestClient, user: FakeUser) -> TestClient:
    login_data = {"username": user.username, "password": user.password}
    login_response = client.post("/auth", data=login_data)
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def category_id(db_session: Any) -> UUID:
    """Create a real category so creator-posts can reference it."""
    repo = CategoryRepository(db_session)
    fake_category = FakeCategory().as_category()
    repo.create_many([fake_category])
    inserted = db_session.query(Category).filter_by(name=fake_category.name).first()
    assert inserted is not None
    return cast(UUID, inserted.id)


def _payload_with_category(fake: FakeCreatorPost, category_id: UUID) -> dict[str, Any]:
    payload = fake.as_dict()
    payload["category_id"] = str(category_id)
    payload["reference_id"] = None
    return payload


def test_should_create_post(test_client: TestClient, category_id: UUID) -> None:
    post = FakeCreatorPost()
    r = test_client.post(
        "/creator-posts", json=_payload_with_category(post, category_id)
    )
    assert r.status_code == 201, r.text
    assert r.json()["feed_post"]["post"]["description"] == post.description


def test_should_like_dislike_unlike_creator_post(
    test_client: TestClient, category_id: UUID
) -> None:
    created = test_client.post(
        "/creator-posts", json=_payload_with_category(FakeCreatorPost(), category_id)
    )
    assert created.status_code == 201, created.text
    post = created.json()["feed_post"]["post"]

    assert test_client.post(f"/creator-posts/{post['id']}/like").status_code == 200
    assert test_client.post(f"/creator-posts/{post['id']}/unlike").status_code == 200
    assert test_client.post(f"/creator-posts/{post['id']}/dislike").status_code == 200


def test_should_comment_and_delete_creator_post(
    test_client: TestClient, category_id: UUID
) -> None:
    created = test_client.post(
        "/creator-posts", json=_payload_with_category(FakeCreatorPost(), category_id)
    )
    assert created.status_code == 201, created.text
    post = created.json()["feed_post"]["post"]

    comment_res = test_client.post(
        f"/creator-posts/{post['id']}/comments", json={"content": "test comment"}
    )
    assert comment_res.status_code == 201

    comment_id = comment_res.json().get("comment_id")
    if comment_id:
        del_res = test_client.delete(
            f"/creator-posts/{post['id']}/comments/{comment_id}"
        )
        assert del_res.status_code == 204


def test_should_save_and_remove_save_creator_post(
    test_client: TestClient, category_id: UUID
) -> None:
    created = test_client.post(
        "/creator-posts", json=_payload_with_category(FakeCreatorPost(), category_id)
    )
    assert created.status_code == 201, created.text
    post = created.json()["feed_post"]["post"]

    assert test_client.post(f"/creator-posts/{post['id']}/save").status_code == 200
    assert test_client.delete(f"/creator-posts/{post['id']}/save").status_code == 204


def test_should_get_user_creator_posts(
    test_client: TestClient, user: FakeUser, category_id: UUID
) -> None:
    _ = test_client.post(
        "/creator-posts", json=_payload_with_category(FakeCreatorPost(), category_id)
    )
    _ = test_client.post(
        "/creator-posts", json=_payload_with_category(FakeCreatorPost(), category_id)
    )

    r = test_client.get(
        f"/users/{user.id}/creator_posts",
        params={"before": datetime.now().isoformat(), "limit": 10},
    )
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["feed_posts"], list)
    assert len(r.json()["feed_posts"]) >= 2


def test_should_list_my_saved_creator_posts(
    test_client: TestClient, category_id: UUID
) -> None:
    created = test_client.post(
        "/creator-posts", json=_payload_with_category(FakeCreatorPost(), category_id)
    )
    assert created.status_code == 201, created.text
    post = created.json()["feed_post"]["post"]

    assert test_client.post(f"/creator-posts/{post['id']}/save").status_code == 200

    r = test_client.get(
        "/creator-posts/saves",
        params={"before": datetime.now().isoformat(), "limit": 10},
    )
    assert r.status_code == 200, r.text
    saved = r.json()["feed_posts"]
    assert isinstance(saved, list)
    assert any(fp["post"]["id"] == post["id"] for fp in saved)


def test_should_delete_creator_post(test_client: TestClient, category_id: UUID) -> None:
    created = test_client.post(
        "/creator-posts", json=_payload_with_category(FakeCreatorPost(), category_id)
    )
    assert created.status_code == 201, created.text
    post = created.json()["feed_post"]["post"]

    r = test_client.delete(f"/creator-posts/{post['id']}")
    assert r.status_code == 204
