from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import JSONResponse

from src.core.errors import ExistsError
from src.core.users import User
from src.infra.fastapi.dependables import UserRepositoryDependable
from src.infra.services.user import UserService

user_api = APIRouter(tags=["Users"])


def extract_user_fields(user: User) -> dict[str, Any]:
    return {
        "mail": user.mail,
        "password": user.password,
    }


class CreateUserRequest(BaseModel):
    mail: str
    password: str


class UserItem(BaseModel):
    mail: str
    password: str


class UserItemEnvelope(BaseModel):
    user: UserItem


@user_api.post(
    "/users",
    status_code=201,
    response_model=UserItemEnvelope,
)
def register(
    request: CreateUserRequest, users: UserRepositoryDependable
) -> dict[str, Any] | JSONResponse:
    try:
        user = User(**request.model_dump())
        UserService(users).register(user)
        response_data = extract_user_fields(user)
        return {"user": response_data}

    except ExistsError:
        return JSONResponse(
            status_code=409,
            content={"message": "User already exists."},
        )
