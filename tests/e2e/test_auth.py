import requests

from tests.e2e.conftest import BASE_URL, MAIL, PASSWORD


def test_auth_should_success() -> None:
    response = requests.post(
        f"{BASE_URL}/auth", data={"username": MAIL, "password": PASSWORD}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_auth_should_fail() -> None:
    response = requests.post(
        f"{BASE_URL}/auth", data={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401
