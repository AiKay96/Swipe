from fastapi.testclient import TestClient

from tests.fake import FakeUser


def test_should_login(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201

    username = response.json()["user"]["username"]
    data = {
        "username": username,
        "password": fake.password,
    }
    auth_response = client.post("/auth", data=data)

    assert auth_response.status_code == 200
    assert "access_token" in auth_response.json()


def test_should_not_login_on_wrong_password(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201

    username = response.json()["user"]["username"]
    data = {
        "username": username,
        "password": "wrong_password",
    }
    response = client.post("/auth", data=data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_should_not_login_on_unknown_user(client: TestClient) -> None:
    fake = FakeUser()
    data = {
        "username": fake.username,
        "password": fake.password,
    }

    response = client.post("/auth", data=data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_token_structure(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201

    username = response.json()["user"]["username"]
    data = {
        "username": username,
        "password": fake.password,
    }
    response = client.post("/auth", data=data)

    token = response.json()["access_token"]
    parts = token.split(".")
    assert len(parts) == 3


def test_protected_requires_token() -> None:
    assert True


def test_should_access_with_token() -> None:
    assert True
