from typing import Any

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.responses import JSONResponse

from src.core.errors import DoesNotExistError
from src.core.users import User
from src.infra.fastapi.dependables import (
    UserRepositoryDependable,
    get_current_user,
    get_refresh_token,
)
from src.infra.services.auth import AuthService
from src.runner.config import settings

auth_api = APIRouter(tags=["Authentication"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str


@auth_api.post(
    "/auth",
    status_code=200,
    response_model=TokenResponse,
)
def login(
    response: Response,
    users: UserRepositoryDependable,
    form_data: OAuth2PasswordRequestForm = Depends(),  # noqa: B008
) -> dict[str, str] | JSONResponse:
    auth = AuthService(users)
    try:
        access_token, refresh_token = auth.authenticate(
            form_data.username, form_data.password
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.reftesh_token_expire_days * 24 * 60 * 60,
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except DoesNotExistError:
        return JSONResponse(
            status_code=401,
            content={"message": "Invalid credentials."},
        )


@auth_api.post(
    "/logout",
    status_code=200,
)
def logout(
    response: Response,
    _: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    response.delete_cookie("refresh_token", httponly=True)
    return JSONResponse(
        status_code=200,
        content={"message": "Logged out successfully."},
    )


@auth_api.post(
    "/refresh",
    status_code=200,
    response_model=AccessTokenResponse,
)
def refresh_token(
    users: UserRepositoryDependable,
    token: str = Depends(get_refresh_token),
    _: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    auth = AuthService(users)
    try:
        new_access_token = auth.refresh_access_token(token)
        return {"access_token": new_access_token}
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"message": str(e)},
        )
