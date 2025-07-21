from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from src.core.users import User, UserRepository
from src.infra.services.auth import AuthService


def get_user_repository(request: Request) -> UserRepository:
    return request.app.state.users  # type: ignore


UserRepositoryDependable = Annotated[UserRepository, Depends(get_user_repository)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth")


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> User:
    auth = AuthService(get_user_repository(request))
    try:
        return auth.get_user_from_token(token)
    except Exception as err:
        raise HTTPException(status_code=401, detail=str(err)) from err


def get_refresh_token(request: Request) -> str:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing.")
    return refresh_token
