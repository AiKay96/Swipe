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
    assert response.json() == {"message": "Invalid credentials."}


def test_should_not_login_on_unknown_user(client: TestClient) -> None:
    fake = FakeUser()
    data = {
        "username": fake.username,
        "password": fake.password,
    }

    response = client.post("/auth", data=data)

    assert response.status_code == 401
    assert response.json() == {"message": "Invalid credentials."}


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


def test_should_refresh_token(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201

    username = response.json()["user"]["username"]
    login_data = {"username": username, "password": fake.password}
    login_response = client.post("/auth", data=login_data)
    assert login_response.status_code == 200

    refresh_token = login_response.cookies.get("refresh_token")
    access_token = login_response.json()["access_token"]
    assert refresh_token
    assert access_token

    client.cookies.set("refresh_token", refresh_token)
    headers = {"Authorization": f"Bearer {access_token}"}
    refresh_response = client.post("/refresh", headers=headers)

    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()


def test_should_not_refresh_invalid_token(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201

    username = response.json()["user"]["username"]

    login_response = client.post(
        "/auth", data={"username": username, "password": fake.password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    client.cookies.set("refresh_token", "invalid.token")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/refresh", headers=headers)

    assert response.status_code == 401


def test_protected_requires_token(client: TestClient) -> None:
    response = client.get("/me")
    assert response.status_code == 401


def test_should_access_with_token(client: TestClient) -> None:
    fake = FakeUser()
    create_response = client.post("/users", json=fake.as_create_dict())
    username = create_response.json()["user"]["username"]

    login_response = client.post(
        "/auth",
        data={
            "username": username,
            "password": fake.password,
        },
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["user"]["username"] == username


def test_should_logout_and_clear_cookie(client: TestClient) -> None:
    fake = FakeUser()
    create_response = client.post("/users", json=fake.as_create_dict())
    username = create_response.json()["user"]["username"]

    login_response = client.post(
        "/auth",
        data={
            "username": username,
            "password": fake.password,
        },
    )

    assert login_response.status_code == 200
    assert "refresh_token" in login_response.cookies

    refresh_token = login_response.cookies["refresh_token"]
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    client.cookies.set("refresh_token", refresh_token)
    logout_response = client.post("/logout", headers=headers)

    assert logout_response.status_code == 200
    assert logout_response.cookies.get("refresh_token") is None
    assert logout_response.json()["message"] == "Logged out successfully."

    client.cookies.set("refresh_token", refresh_token)
    refresh_attempt = client.post("/refresh", headers=headers)

    assert refresh_attempt.status_code == 401
    assert refresh_attempt.json() == {"message": "Refresh token not recognized"}
