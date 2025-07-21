import requests

from tests.e2e.conftest import BASE_URL


def test_auth_should_success(test_user: dict[str, str]) -> None:
    response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_auth_should_fail() -> None:
    response = requests.post(
        f"{BASE_URL}/auth",
        data={"username": "wrong", "password": "wrong"},
    )
    assert response.status_code == 401
