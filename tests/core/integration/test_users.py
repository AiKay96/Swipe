from fastapi.testclient import TestClient

from tests.fake import FakeUser


def test_should_create(client: TestClient) -> None:
    user = FakeUser().as_create_dict()
    response = client.post("/users", json=user)

    assert response.status_code == 201
    assert response.json()["user"]["mail"] == user["mail"]
    assert "username" in response.json()["user"]
    assert "display_name" in response.json()["user"]
    assert "password" not in response.json()["user"]


def test_should_not_create_same(client: TestClient) -> None:
    user = FakeUser().as_create_dict()

    response = client.post("/users", json=user)
    assert response.status_code == 201

    response = client.post("/users", json=user)
    assert response.status_code == 409
    assert response.json() == {"message": "User already exists."}
