from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.responses import JSONResponse

from src.core.errors import DoesNotExistError, ExistsError
from src.core.users import User
from src.infra.fastapi.dependables import UserRepositoryDependable, get_current_user
from src.infra.services.user import UserService

user_api = APIRouter(tags=["Users"])


def extract_user_fields(user: User) -> dict[str, Any]:
    return {
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
    }


def extract_me_fields(user: User) -> dict[str, Any]:
    return {
        "mail": user.mail,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
    }


class CreateUserRequest(BaseModel):
    mail: str
    password: str


class UserItem(BaseModel):
    username: str
    display_name: str
    bio: str | None


class UserItemEnvelope(BaseModel):
    user: UserItem


class MeItem(BaseModel):
    mail: str
    username: str
    display_name: str
    bio: str | None


class MeItemEnvelope(BaseModel):
    user: MeItem


@user_api.post(
    "/users",
    status_code=201,
    response_model=UserItemEnvelope,
)
def register(
    request: CreateUserRequest, users: UserRepositoryDependable
) -> dict[str, Any] | JSONResponse:
    try:
        service = UserService(users)
        user = service.register(request.mail, request.password)
        return {"user": extract_user_fields(user)}

    except ExistsError:
        return JSONResponse(
            status_code=409,
            content={"message": "User already exists."},
        )


@user_api.get(
    "/users/{username}",
    status_code=200,
    response_model=UserItemEnvelope,
)
def get_user(
    username: str, users: UserRepositoryDependable
) -> dict[str, Any] | JSONResponse:
    try:
        user = UserService(users).get_by_username(username)
        return {"user": extract_user_fields(user)}
    except DoesNotExistError:
        return JSONResponse(
            status_code=404,
            content={"message": "User not found."},
        )


@user_api.get(
    "/me",
    status_code=200,
    response_model=MeItemEnvelope,
)
def get_me(user: User = Depends(get_current_user)) -> dict[str, Any]:  # noqa: B008
    return {"user": extract_me_fields(user)}
