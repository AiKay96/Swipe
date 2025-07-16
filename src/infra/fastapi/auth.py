from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from src.core.errors import DoesNotExistError
from src.infra.fastapi.dependables import UserRepositoryDependable
from src.infra.services.auth import AuthService

auth_api = APIRouter(tags=["Authentication"])


class LoginRequest(BaseModel):
    mail: str
    password: str


@auth_api.post("/auth")
def login(
    users: UserRepositoryDependable,
    form_data: OAuth2PasswordRequestForm = Depends(),  # noqa: B008
) -> dict[str, str]:
    auth = AuthService(users)
    try:
        token = auth.authenticate(form_data.username, form_data.password)
        return {"access_token": token, "token_type": "bearer"}
    except DoesNotExistError as err:
        raise HTTPException(status_code=401, detail="Invalid credentials") from err
