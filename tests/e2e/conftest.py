import pytest
import requests

from src.runner.config import settings
from tests.fake import FakeUser

BASE_URL = settings.base_url


@pytest.fixture(scope="session")
def test_user() -> dict[str, str]:
    user = FakeUser()
    create = requests.post(f"{BASE_URL}/users", json=user.as_create_dict())

    assert create.status_code == 201
    return {
        **create.json()["user"],
        "password": user.password,
    }
