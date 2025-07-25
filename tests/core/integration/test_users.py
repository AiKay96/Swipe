import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.infra.fastapi.users import UserUpdateRequest
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

    login_data = {"username": username, "password": fake.password}
    login_response = client.post("/auth", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    get_response = client.get(
        f"/users/{username}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200

    user = get_response.json()["user"]
    assert user["username"] == username
    assert "mail" not in user
    assert "password" not in user


def test_should_not_get_unknown_user(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201
    username = response.json()["user"]["username"]

    login_data = {"username": username, "password": fake.password}
    login_response = client.post("/auth", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        f"/users/{FakeUser().username}", headers={"Authorization": f"Bearer {token}"}
    )

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


def test_should_update_me(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201

    username = response.json()["user"]["username"]
    login_response = client.post(
        "/auth", data={"username": username, "password": fake.password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    update_user = FakeUser()
    update_data = {"display_name": update_user.display_name, "bio": update_user.bio}
    response = client.patch(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
        json=update_data,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User updated successfully."


def test_should_not_update_to_existing_username(client: TestClient) -> None:
    user1 = FakeUser()
    user2 = FakeUser()

    r1 = client.post("/users", json=user1.as_create_dict())
    r2 = client.post("/users", json=user2.as_create_dict())
    assert r1.status_code == 201
    assert r2.status_code == 201

    username1 = r1.json()["user"]["username"]
    username2 = r2.json()["user"]["username"]

    login_response = client.post(
        "/auth", data={"username": username1, "password": user1.password}
    )
    token = login_response.json()["access_token"]

    response = client.patch(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": username2},
    )

    assert response.status_code == 409
    assert response.json() == {"message": "Username already taken."}


def test_should_update_username_only(client: TestClient) -> None:
    fake = FakeUser()
    response = client.post("/users", json=fake.as_create_dict())
    assert response.status_code == 201
    old_username = response.json()["user"]["username"]

    login_response = client.post(
        "/auth", data={"username": old_username, "password": fake.password}
    )
    token = login_response.json()["access_token"]

    new_username = FakeUser().username
    patch_response = client.patch(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": new_username},
    )

    assert patch_response.status_code == 200

    get_response = client.get(
        f"/users/{new_username}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200

def test_should_update_all_fields(client: TestClient) -> None:
    user = FakeUser()
    r = client.post("/users", json=user.as_create_dict())
    login = client.post("/auth", data={"username": r.json()["user"]["username"], "password": user.password})
    token = login.json()["access_token"]

    new_user = FakeUser()
    update_data = {
        "username": new_user.username,
        "display_name": new_user.display_name,
        "bio": new_user.bio,
    }

    patch = client.patch("/me", headers={"Authorization": f"Bearer {token}"}, json=update_data)
    assert patch.status_code == 200

    get = client.get(f"/users/{new_user.username}", headers={"Authorization": f"Bearer {token}"})
    assert get.status_code == 200
    assert get.json()["user"]["display_name"] == new_user.display_name
    assert get.json()["user"]["bio"] == new_user.bio

def test_should_fail_get_me_unauthorized(client: TestClient) -> None:
    response = client.get("/me")
    assert response.status_code == 401

def test_should_fail_get_user_unauthorized(client: TestClient) -> None:
    response = client.get("/users/someuser")
    assert response.status_code == 401

@pytest.mark.parametrize(
    "username",
    [
        "AiKay",  # mixed case
        "username_123",  # underscores + digits
        "A1b2c3",  # letters and numbers
        "A" * 30,  # max length
    ],
)
def test_should_update_valid_usernames(username: str) -> None:
    req = UserUpdateRequest(username=username)
    assert req.username == username


@pytest.mark.parametrize(
    "username",
    [
        "1username",  # starts with digit
        "_username",  # starts with underscore
        "a",  # too short
        "a@b",  # invalid character
        "a.b",  # dot not allowed
        "a-b",  # dash not allowed
        "a b",  # space not allowed
        "A" * 31,  # too long
    ],
)
def test_should_not_update_invalid_usernames(username: str) -> None:
    with pytest.raises(ValidationError):
        UserUpdateRequest(username=username)


@pytest.mark.parametrize(
    "display_name",
    [
        "",  # empty
        "  ",  # spaces only
        "ab",  # too short
        "A" * 65,  # too long
    ],
)
def test_should_not_update_invalid_display_names(display_name: str) -> None:
    with pytest.raises(ValidationError):
        UserUpdateRequest(display_name=display_name)


@pytest.mark.parametrize(
    "bio",
    [
        "",  # empty
        " ",  # spaces only
        "a",  # too short
        "A" * 65,  # too long
    ],
)
def test_invalid_bios(bio: str) -> None:
    with pytest.raises(ValidationError):
        UserUpdateRequest(bio=bio)
