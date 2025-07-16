import contextlib

import pytest
import requests

from src.runner.config import settings

BASE_URL = settings.base_url
MAIL = settings.mail
PASSWORD = settings.password


@pytest.fixture(scope="session", autouse=True)
def ensure_user_exists() -> None:
    user = {
        "mail": MAIL,
        "password": PASSWORD,
    }

    with contextlib.suppress(Exception):
        requests.post(f"{BASE_URL}/users", json=user)

    return
