from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from src.core.errors import DoesNotExistError
from src.core.users import User, UserRepository
from src.runner.config import settings


@dataclass
class AuthService:
    users: UserRepository

    def create_access_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": datetime.utcnow()
            + timedelta(minutes=settings.access_token_expire_minutes),
        }
        return str(
            jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        )

    def create_refresh_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.utcnow()
            + timedelta(days=settings.reftesh_token_expire_days),
        }
        return str(
            jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        )

    def authenticate(self, username: str, password: str) -> tuple[str, str]:
        user = self.users.find_by_username(username)
        if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
            raise DoesNotExistError("Invalid credentials")

        return (
            self.create_access_token(str(user.id)),
            self.create_refresh_token(str(user.id)),
        )

    def decode_token(self, token: str, expected_type: str = "access") -> str:
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            if payload.get("type") != expected_type:
                raise JWTError("Token type mismatch")
            return str(payload["sub"])
        except JWTError as err:
            raise DoesNotExistError("Invalid or expired token") from err

    def get_user_from_token(self, token: str) -> User:
        user_id = self.decode_token(token, expected_type="access")
        user = self.users.read_by(user_id=UUID(user_id))
        if not user:
            raise DoesNotExistError("User not found")
        return user

    def refresh_access_token(self, refresh_token: str) -> str:
        user_id = self.decode_token(refresh_token, expected_type="refresh")
        return self.create_access_token(user_id)
