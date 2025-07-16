from fastapi.testclient import TestClient

from tests.fake import Fake


def test_should_create(client: TestClient) -> None:
    user = Fake().user_dict()
    response = client.post("/users", json=user)

    assert response.status_code == 201
    assert response.json() == {"user": {**user}}


def test_should_not_create_same(client: TestClient) -> None:
    user = Fake().user_dict()

    response = client.post("/users", json=user)
    assert response.status_code == 201

    response = client.post("/users", json=user)
    assert response.status_code == 409
    assert response.json() == {"message": "User already exists."}
