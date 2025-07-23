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
    response = requests.post(
        f"{BASE_URL}/refresh", cookies={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
