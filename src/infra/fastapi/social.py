from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.users import User
from src.infra.fastapi.dependables import (
    SocialServiceDependable,
    get_current_user,
)
from src.infra.fastapi.utils import exception_response

social_api = APIRouter(tags=["Social"])


class UserItem(BaseModel):
    id: UUID
    username: str
    display_name: str

    @classmethod
    def from_user(cls, user: User) -> "UserItem":
        return cls(id=user.id, username=user.username, display_name=user.display_name)


class FollowRequest(BaseModel):
    target_id: UUID


class FriendRequestBody(BaseModel):
    to_user_id: UUID


class UserListEnvelope(BaseModel):
    users: list[UserItem]


@social_api.post(
    "/follow",
    status_code=200,
)
def follow_user(
    body: FollowRequest,
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.follow(user.id, body.target_id)
        return JSONResponse(
            status_code=200, content={"message": "Followed successfully."}
        )
    except Exception as e:
        return exception_response(e)


@social_api.post(
    "/unfollow",
    status_code=200,
)
def unfollow_user(
    body: FollowRequest,
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.unfollow(user.id, body.target_id)
        return JSONResponse(
            status_code=200, content={"message": "Unfollowed successfully."}
        )
    except Exception as e:
        return exception_response(e)


@social_api.post(
    "/friend-requests/send",
    status_code=201,
)
def send_friend_request(
    body: FriendRequestBody,
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.send_friend_request(user.id, body.to_user_id)
        return JSONResponse(
            status_code=201, content={"message": "Friend request sent."}
        )
    except Exception as e:
        return exception_response(e)


@social_api.post(
    "/friend-requests/cancel",
    status_code=200,
)
def cancel_friend_request(
    body: FriendRequestBody,
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.cancel_friend_request(user.id, body.to_user_id)
        return JSONResponse(
            status_code=200, content={"message": "Friend request canceled."}
        )
    except Exception as e:
        return exception_response(e)


@social_api.post(
    "/friend-requests/accept",
    status_code=200,
)
def accept_friend_request(
    body: FriendRequestBody,
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.accept_friend_request(body.to_user_id, user.id)
        return JSONResponse(
            status_code=200, content={"message": "Friend request accepted."}
        )
    except Exception as e:
        return exception_response(e)


@social_api.post(
    "/friend-requests/decline",
    status_code=200,
)
def decline_friend_request(
    body: FriendRequestBody,
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.decline_friend_request(body.to_user_id, user.id)
        return JSONResponse(
            status_code=200, content={"message": "Friend request declined."}
        )
    except Exception as e:
        return exception_response(e)


@social_api.get(
    "/followers",
    response_model=UserListEnvelope,
    status_code=200,
)
def get_followers(
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        return {
            "users": [UserItem.from_user(u) for u in service.get_followers(user.id)]
        }
    except Exception as e:
        return exception_response(e)


@social_api.get(
    "/following",
    response_model=UserListEnvelope,
    status_code=200,
)
def get_following(
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        return {
            "users": [UserItem.from_user(u) for u in service.get_following(user.id)]
        }
    except Exception as e:
        return exception_response(e)


@social_api.get(
    "/friends",
    response_model=UserListEnvelope,
    status_code=200,
)
def get_friends(
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        return {"users": [UserItem.from_user(u) for u in service.get_friends(user.id)]}
    except Exception as e:
        return exception_response(e)


@social_api.get(
    "/friend-requests/incoming",
    response_model=UserListEnvelope,
    status_code=200,
)
def get_incoming_friend_requests(
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        return {
            "users": [
                UserItem.from_user(u)
                for u in service.get_incoming_friend_requests(user.id)
            ]
        }
    except Exception as e:
        return exception_response(e)
