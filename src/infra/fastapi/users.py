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
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
    }


class CreateUserRequest(BaseModel):
    mail: str
    password: str


class UserItem(BaseModel):
    mail: str
    username: str
    display_name: str
    bio: str | None


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
        service = UserService(users)
        service.register(request.mail, request.password)
        user = service.get_by_mail(request.mail)
        return {"user": extract_user_fields(user)}

    except ExistsError:
        return JSONResponse(
            status_code=409,
            content={"message": "User already exists."},
        )
