import requests

from tests.e2e.conftest import BASE_URL


def test_auth_should_success(test_user: dict[str, str]) -> None:
    response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 200

    json = response.json()
    assert "access_token" in json
    assert "token_type" in json
    assert "refresh_token" not in json

    assert "refresh_token" in response.cookies


def test_auth_should_fail() -> None:
    response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": "wrong", "password": "wrong"},
    )
    assert response.status_code == 401


def test_refresh_token_flow(test_user: dict[str, str]) -> None:
    auth_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert auth_response.status_code == 200

    refresh_token = auth_response.cookies.get("refresh_token")
    assert refresh_token

    access_token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.post(
        f"{BASE_URL}/refresh", headers=headers, cookies={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_logout_should_clear_cookie(test_user: dict[str, str]) -> None:
    auth_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert auth_response.status_code == 200
    refresh_token = auth_response.cookies.get("refresh_token")
    assert refresh_token

    headers = {
        "Authorization": f"Bearer {auth_response.json()['access_token']}",
    }

    logout_response = requests.post(
        f"{BASE_URL}/logout", cookies={"refresh_token": refresh_token}, headers=headers
    )

    assert logout_response.status_code == 200
    assert logout_response.cookies.get("refresh_token") is None
    assert logout_response.json()["message"] == "Logged out successfully."


def test_refresh_should_fail_without_auth(test_user: dict[str, str]) -> None:
    auth_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert auth_response.status_code == 200

    refresh_token = auth_response.cookies.get("refresh_token")
    assert refresh_token

    response = requests.post(
        f"{BASE_URL}/refresh", cookies={"refresh_token": refresh_token}
    )

    assert response.status_code == 401


def test_logout_should_fail_without_token() -> None:
    response = requests.post(f"{BASE_URL}/logout")
    assert response.status_code == 401


def test_should_invalidate_refresh_token_after_logout(
    test_user: dict[str, str],
) -> None:
    auth_response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert auth_response.status_code == 200

    access_token = auth_response.json()["access_token"]
    refresh_token = auth_response.cookies.get("refresh_token")
    assert access_token
    assert refresh_token

    logout_response = requests.post(
        f"{BASE_URL}/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 200

    reuse_response = requests.post(
        f"{BASE_URL}/refresh",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"refresh_token": refresh_token},
    )

    assert reuse_response.status_code == 401
