from dataclasses import replace
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from tests.fake import FakePersonalPost, FakeUser


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


def test_should_create_post(test_client: TestClient) -> None:
    post = FakePersonalPost()
    r = test_client.post("/posts", json=post.as_dict())
    assert r.status_code == 201
    assert r.json()["post"]["description"] == post.description


def test_should_like_dislike_unlike_post(test_client: TestClient) -> None:
    post = test_client.post("/posts", json=FakePersonalPost().as_dict()).json()["post"]

    assert test_client.post(f"/posts/{post['id']}/like").status_code == 200
    assert test_client.post(f"/posts/{post['id']}/unlike").status_code == 200
    assert test_client.post(f"/posts/{post['id']}/dislike").status_code == 200


def test_should_comment_and_delete(test_client: TestClient) -> None:
    post = test_client.post("/posts", json=FakePersonalPost().as_dict()).json()["post"]

    comment_res = test_client.post(
        f"/posts/{post['id']}/comments", json={"content": "test comment"}
    )
    assert comment_res.status_code == 201

    comment_id = comment_res.json().get("comment_id")
    if comment_id:
        del_res = test_client.delete(f"/posts/{post['id']}/comments/{comment_id}")
        assert del_res.status_code == 204


def test_should_change_privacy(test_client: TestClient) -> None:
    post = test_client.post(
        "/posts",
        json=FakePersonalPost().as_dict(),
    ).json()["post"]

    r = test_client.post(f"/posts/{post['id']}/privacy")
    assert r.status_code == 200


def test_should_get_user_posts(test_client: TestClient, user: FakeUser) -> None:
    post = test_client.post(
        "/posts",
        json=FakePersonalPost().as_dict(),
    ).json()["post"]
    test_client.post(f"/posts/{post['id']}/privacy")
    r = test_client.get(
        f"/users/{user.id}/personal_posts",
        params={"before": datetime.now().isoformat(), "limit": 10},
    )

    assert r.status_code == 200
    assert len(r.json()["posts"]) == 1


def test_should_delete_post(test_client: TestClient) -> None:
    post = test_client.post(
        "/posts",
        json=FakePersonalPost().as_dict(),
    ).json()["post"]

    r = test_client.delete(f"/posts/{post['id']}")
    assert r.status_code == 204
