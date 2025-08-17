import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from starlette.responses import JSONResponse

from src.core.errors import DoesNotExistError, ExistsError
from src.core.social import FriendStatus
from src.core.users import User
from src.infra.fastapi.dependables import (
    FeedServiceDependable,
    SocialServiceDependable,
    UserRepositoryDependable,
    get_current_user,
)
from src.infra.services.user import UserService

user_api = APIRouter(tags=["Users"])

USERNAME_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{2,29}$")


class CreateUserRequest(BaseModel):
    mail: str
    password: str


class UserItem(BaseModel):
    id: UUID
    username: str
    display_name: str
    bio: str | None
    friend_status: FriendStatus
    is_following: bool

    @classmethod
    def from_user(
        cls, user: User, friend_status: FriendStatus, is_following: bool
    ) -> "UserItem":
        return cls(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
            friend_status=friend_status,
            is_following=is_following,
        )


class UserItemEnvelope(BaseModel):
    user: UserItem


class MeItem(BaseModel):
    id: UUID
    mail: str
    username: str
    display_name: str
    bio: str | None

    @classmethod
    def from_user(cls, user: User) -> "MeItem":
        return cls(
            id=user.id,
            mail=user.mail,
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
        )


class MeItemEnvelope(BaseModel):
    user: MeItem


class UserUpdateRequest(BaseModel):
    username: str | None = None
    display_name: str | None = None
    bio: str | None = None

    @field_validator("username")
    @classmethod
    def username_validate(cls, v: str) -> str:
        if v is None:
            return v
        v = v.strip()
        if not USERNAME_REGEX.match(v):
            raise ValueError("Invalid username")
        return v

    @field_validator("display_name")
    @classmethod
    def display_name_validate(cls, v: str) -> str:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Display name cannot be empty")
        if len(v) < 3:
            raise ValueError("Display name is too short")
        if len(v) > 64:
            raise ValueError("Display name is too long")
        return v

    @field_validator("bio")
    @classmethod
    def bio_validate(cls, v: str) -> str:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Bio cannot be empty")
        if len(v) < 3:
            raise ValueError("Bio is too short")
        if len(v) > 64:
            raise ValueError("Bio is too long")
        return v


@user_api.post(
    "/users",
    status_code=201,
    response_model=MeItemEnvelope,
)
def register(
    request: CreateUserRequest,
    users: UserRepositoryDependable,
    feed: FeedServiceDependable,
) -> dict[str, Any] | JSONResponse:
    try:
        service = UserService(users)
        user = service.register(request.mail, request.password)
        feed.init_preferences(user.id)
        return {"user": MeItem.from_user(user)}

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
    username: str,
    users: UserRepositoryDependable,
    social: SocialServiceDependable,
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        user = UserService(users).get_by_username(username)
        friend_status = social.get_friend_status(current_user.id, user.id)
        is_following = social.is_following(current_user.id, user.id)
        return {"user": UserItem.from_user(user, friend_status, is_following)}
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
    return {"user": MeItem.from_user(user)}


@user_api.patch(
    "/me",
    status_code=200,
    response_model=MeItemEnvelope,
)
def update_me(
    request: UserUpdateRequest,
    users: UserRepositoryDependable,
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    service = UserService(users)
    try:
        service.update_user(
            user_id=current_user.id,
            **request.model_dump(exclude_unset=True, exclude_none=True),
        )
        return JSONResponse(
            status_code=200, content={"message": "User updated successfully."}
        )
    except DoesNotExistError:
        return JSONResponse(
            status_code=404,
            content={"message": "User not found."},
        )
    except ExistsError:
        return JSONResponse(
            status_code=409,
            content={"message": "Username already taken."},
        )
    except Exception as e:
        return JSONResponse(
            status_code=409,
            content={"message": str(e)},
        )
