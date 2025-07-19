from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import bcrypt
from jose import jwt

from src.core.errors import DoesNotExistError
from src.core.users import UserRepository
from src.runner.config import settings


@dataclass
class AuthService:
    users: UserRepository

    def authenticate(self, mail: str, password: str) -> Any:
        user = self.users.read_by_mail(mail)
        if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
            raise DoesNotExistError("Invalid credentials")

        payload = {
            "sub": user.mail,
            "exp": datetime.utcnow()
            + timedelta(minutes=settings.access_token_expire_minutes),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
