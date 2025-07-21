from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.core.errors import DoesNotExistError
from src.infra.fastapi.dependables import UserRepositoryDependable, get_refresh_token
from src.infra.services.auth import AuthService
from src.runner.config import settings

auth_api = APIRouter(tags=["Authentication"])


@auth_api.post("/auth")
def login(
    response: Response,
    users: UserRepositoryDependable,
    form_data: OAuth2PasswordRequestForm = Depends(),  # noqa: B008
) -> dict[str, str]:
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
    except DoesNotExistError as err:
        raise HTTPException(status_code=401, detail="Invalid credentials") from err


@auth_api.post("/refresh")
def refresh_token(
    users: UserRepositoryDependable,
    token: str = Depends(get_refresh_token),
) -> dict[str, str]:
    auth = AuthService(users)
    try:
        new_access_token = auth.refresh_access_token(token)
        return {"access_token": new_access_token}
    except Exception as err:
        raise HTTPException(status_code=401, detail=str(err)) from err
