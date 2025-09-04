from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from tests.fake import FakeUser


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


def test_follow_unfollow_user(authed_client: TestClient, user_b: FakeUser) -> None:
    res = authed_client.post("/follow", json={"target_id": user_b.id})
    assert res.status_code == 200

    res = authed_client.post("/unfollow", json={"target_id": user_b.id})
    assert res.status_code == 200


def test_friend_request_flow(
    authed_client: TestClient, user_a: FakeUser, user_b: FakeUser
) -> None:
    res = authed_client.post("/friend-requests/send", json={"to_user_id": user_b.id})
    assert res.status_code == 201

    res = authed_client.post("/friend-requests/cancel", json={"to_user_id": user_b.id})
    assert res.status_code == 200

    res = authed_client.post("/friend-requests/send", json={"to_user_id": user_b.id})
    assert res.status_code == 201

    login = authed_client.post(
        "/auth", data={"username": user_b.username, "password": user_b.password}
    )
    token = login.json()["access_token"]
    authed_client.headers.update({"Authorization": f"Bearer {token}"})

    res = authed_client.post("/friend-requests/accept", json={"to_user_id": user_a.id})
    assert res.status_code == 200


def test_decline_friend_request(
    authed_client: TestClient, user_a: FakeUser, user_b: FakeUser
) -> None:
    res = authed_client.post("/friend-requests/send", json={"to_user_id": user_b.id})
    assert res.status_code == 201

    login = authed_client.post(
        "/auth", data={"username": user_b.username, "password": user_b.password}
    )
    token = login.json()["access_token"]
    authed_client.headers.update({"Authorization": f"Bearer {token}"})

    res = authed_client.post("/friend-requests/decline", json={"to_user_id": user_a.id})
    assert res.status_code == 200
