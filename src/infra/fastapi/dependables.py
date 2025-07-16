from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.core.users import UserRepository
from src.runner.config import settings


def get_user_repository(request: Request) -> UserRepository:
    return request.app.state.users  # type: ignore


UserRepositoryDependable = Annotated[UserRepository, Depends(get_user_repository)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth")


def get_current_user(token: str = Depends(oauth2_scheme)) -> Any:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload["sub"]
    except JWTError as err:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from err
