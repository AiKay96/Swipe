from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

import bcrypt
from jose import JWTError, jwt

from src.core.errors import DoesNotExistError
from src.core.tokens import TokenRepository
from src.core.users import User, UserRepository
from src.runner.config import settings


@dataclass
class AuthService:
    users: UserRepository
    tokens: TokenRepository

    def create_access_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": datetime.now()
            + timedelta(minutes=settings.access_token_expire_minutes),
        }
        return str(
            jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        )

    def create_refresh_token(self, user_id: str) -> str:
        jti = uuid4()
        expires = datetime.now() + timedelta(days=settings.reftesh_token_expire_days)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "jti": str(jti),
            "exp": datetime.now() + timedelta(days=settings.reftesh_token_expire_days),
        }
        self.tokens.save(jti, UUID(user_id), expires)
        return str(
            jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        )

    def authenticate(self, unique: str, password: str) -> tuple[str, str]:
        user = self.users.read_by(username=unique)
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return (
                self.create_access_token(str(user.id)),
                self.create_refresh_token(str(user.id)),
            )
        user = self.users.read_by(mail=unique)
        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            return (
                self.create_access_token(str(user.id)),
                self.create_refresh_token(str(user.id)),
            )

        raise DoesNotExistError("Invalid credentials")

    def decode_token(self, token: str, expected_type: str = "access") -> dict[str, Any]:
        try:
            payload = cast(
                dict[str, Any],
                jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm]),
            )
            if payload.get("type") != expected_type:
                raise JWTError("Token type mismatch")
            return payload
        except JWTError as err:
            raise DoesNotExistError("Invalid or expired token") from err

    def get_user_from_token(self, token: str) -> User:
        user_id = self.decode_token(token, expected_type="access")["sub"]
        user = self.users.read_by(user_id=UUID(user_id))
        if not user:
            raise DoesNotExistError("User not found")
        return user

    def refresh_access_token(self, refresh_token: str) -> str:
        payload = self.decode_token(refresh_token, expected_type="refresh")
        jti = UUID(payload["jti"])
        if not self.tokens.exists(jti):
            raise DoesNotExistError("Refresh token not recognized")

        self.tokens.delete(jti)

        return self.create_access_token(payload["sub"])

    def logout(self, refresh_token: str) -> None:
        try:
            payload = self.decode_token(refresh_token, expected_type="refresh")
            jti = UUID(payload["jti"])
            self.tokens.delete(jti)
        except Exception:
            pass
