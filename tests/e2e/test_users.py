import requests

from tests.e2e.conftest import BASE_URL
from tests.fake import FakeUser


def test_should_create_user() -> None:
    user = FakeUser().as_create_dict()
    response = requests.post(f"{BASE_URL}/users", json=user)

    assert response.status_code == 201
    assert "username" in response.json()["user"]
    assert "display_name" in response.json()["user"]
    assert "password" not in response.json()["user"]


def test_should_not_create_duplicate_user() -> None:
    user = FakeUser().as_create_dict()

    response = requests.post(f"{BASE_URL}/users", json=user)
    assert response.status_code == 201

    response = requests.post(f"{BASE_URL}/users", json=user)
    assert response.status_code == 409
    assert response.json() == {"message": "User already exists."}


def test_should_get_me(test_user: dict[str, str]) -> None:
    login_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    token = login_response.json()["access_token"]

    me_response = requests.get(
        f"{BASE_URL}/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert me_response.status_code == 200
    user = me_response.json()["user"]
    assert user["username"] == test_user["username"]


def test_should_get_user() -> None:
    fake = FakeUser()
    response = requests.post(f"{BASE_URL}/users", json=fake.as_create_dict())
    assert response.status_code == 201
    username = response.json()["user"]["username"]

    get_response = requests.get(f"{BASE_URL}/users/{username}")
    assert get_response.status_code == 200

    user = get_response.json()["user"]
    assert user["username"] == username
    assert "mail" not in user
    assert "password" not in user


def test_should_not_get_unknown_user() -> None:
    username = FakeUser().username
    response = requests.get(f"{BASE_URL}/users/{username}")
    assert response.status_code == 404
    assert response.json() == {"message": "User not found."}


def test_should_update_user_profile(test_user: dict[str, str]) -> None:
    login_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    username = FakeUser().username
    update_payload = {
        "username": username,
        "display_name": "Updated Name",
        "bio": "This is my updated bio.",
    }
    update_response = requests.patch(
        f"{BASE_URL}/me", headers=headers, json=update_payload
    )

    assert update_response.status_code == 200
    assert update_response.json()["message"] == "User updated successfully."

    get_response = requests.get(
        f"{BASE_URL}/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert get_response.status_code == 200

    updated_user = get_response.json()["user"]
    assert updated_user["username"] == username
    assert updated_user["display_name"] == "Updated Name"
    assert updated_user["bio"] == "This is my updated bio."


def test_should_fail_update_with_invalid_username(test_user: dict[str, str]) -> None:
    login_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {"username": "invalid@name"}
    response = requests.patch(f"{BASE_URL}/me", headers=headers, json=payload)

    assert response.status_code == 422


def test_should_fail_update_with_taken_username(test_user: dict[str, str]) -> None:
    second_user = FakeUser().as_create_dict()
    create_resp = requests.post(f"{BASE_URL}/users", json=second_user)
    assert create_resp.status_code == 201
    taken_username = create_resp.json()["user"]["username"]

    login_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {"username": taken_username}
    response = requests.patch(f"{BASE_URL}/me", headers=headers, json=payload)

    assert response.status_code == 409
    assert response.json() == {"message": "Username already taken."}


def test_should_fail_update_with_empty_display_name(test_user: dict[str, str]) -> None:
    login_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.patch(
        f"{BASE_URL}/me", headers=headers, json={"display_name": ""}
    )

    assert response.status_code == 422
