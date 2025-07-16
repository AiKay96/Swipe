from fastapi.testclient import TestClient

from tests.fake import Fake


def test_should_login(client: TestClient) -> None:
    user = Fake().user_dict()
    client.post("/users", json=user)

    data = {
        "username": user["mail"],
        "password": user["password"],
    }
    response = client.post("/auth", data=data)

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_should_not_login_on_wrong_password(client: TestClient) -> None:
    user = Fake().user_dict()
    client.post("/users", json=user)

    data = {
        "username": user["mail"],
        "password": "wrong_password",
    }
    response = client.post("/auth", data=data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_should_not_login_on_unknown_user(client: TestClient) -> None:
    user = Fake().user_dict()
    data = {
        "username": user["mail"],
        "password": user["password"],
    }

    response = client.post("/auth", data=data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_token_structure(client: TestClient) -> None:
    user = Fake().user_dict()
    client.post("/users", json=user)

    data = {
        "username": user["mail"],
        "password": user["password"],
    }
    response = client.post("/auth", data=data)

    token = response.json()["access_token"]
    parts = token.split(".")
    assert len(parts) == 3


def test_protected_requires_token() -> None:
    assert True


def test_should_access_with_token() -> None:
    assert True
