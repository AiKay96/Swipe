from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from tests.fake import FakePersonalPost, FakeUser


@pytest.fixture
def user_a(client: TestClient) -> FakeUser:
    user = FakeUser()
    r = client.post("/users", json=user.as_create_dict())
    assert r.status_code == 201
    data = r.json()["user"]
    return replace(user, id=data["id"], username=data["username"])


@pytest.fixture
def user_b(client: TestClient) -> FakeUser:
    user = FakeUser()
    r = client.post("/users", json=user.as_create_dict())
    assert r.status_code == 201
    data = r.json()["user"]
    return replace(user, id=data["id"], username=data["username"])


@pytest.fixture
def authed_client(client: TestClient, user_a: FakeUser) -> TestClient:
    r = client.post(
        "/auth", data={"username": user_a.username, "password": user_a.password}
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_should_get_personal_feed(
    authed_client: TestClient,
    user_a: FakeUser,
    user_b: FakeUser,
) -> None:
    r = authed_client.post("/posts", json=FakePersonalPost().as_dict())
    assert r.status_code == 201

    r = authed_client.post("/friend-requests/send", json={"to_user_id": user_b.id})
    assert r.status_code == 201

    r = authed_client.post(
        "/auth", data={"username": user_b.username, "password": user_b.password}
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    authed_client.headers.update({"Authorization": f"Bearer {token}"})

    authed_client.post("/friend-requests/accept", json={"to_user_id": user_a.id})
    assert r.status_code == 200

    r = authed_client.get(
        "/personal_feed",
        params={"limit": 10},
    )

    assert r.status_code == 200
    assert len(r.json()["posts"]) == 1
