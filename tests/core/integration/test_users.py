from fastapi.testclient import TestClient

from tests.fake import FakeUser


def test_should_create(client: TestClient) -> None:
    user = FakeUser().as_create_dict()
    response = client.post("/users", json=user)

    assert response.status_code == 201
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


def test_should_get_user(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201
    username = response.json()["user"]["username"]

    get_response = client.get(f"/users/{username}")
    assert get_response.status_code == 200

    user = get_response.json()["user"]
    assert user["username"] == username
    assert "mail" not in user
    assert "password" not in user


def test_should_not_get_unknown_user(client: TestClient) -> None:
    username = FakeUser().username
    response = client.get(f"/users/{username}")
    assert response.status_code == 404
    assert response.json() == {"message": "User not found."}


def test_should_get_me(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201
    username = response.json()["user"]["username"]

    login_data = {"username": username, "password": fake.password}
    login_response = client.post("/auth", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert me_response.status_code == 200
    user = me_response.json()["user"]
    assert user["username"] == username
    assert user["mail"] == fake.mail
    assert "password" not in user
