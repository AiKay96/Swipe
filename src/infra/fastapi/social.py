from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.users import User
from src.infra.decorators.user import UserDecorator
from src.infra.fastapi.dependables import (
    SocialServiceDependable,
    get_current_user,
)
from src.infra.fastapi.users import UserItem
from src.infra.fastapi.utils import exception_response

social_api = APIRouter(tags=["Social"])


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


@social_api.post("/suggestions/skip", status_code=200)
def skip_suggestion(
    body: FollowRequest,
    service: SocialServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.skip_suggestion(user.id, body.target_id, 30)
        return JSONResponse(status_code=200, content={"message": "Suggestion skipped."})
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
            "users": [
                UserItem.from_user(
                    UserDecorator(service).decorate_entity(user_id=user.id, user=u)
                )
                for u in service.get_followers(user.id)
            ]
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
            "users": [
                UserItem.from_user(
                    UserDecorator(service).decorate_entity(user_id=user.id, user=u)
                )
                for u in service.get_following(user.id)
            ]
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
        return {
            "users": [
                UserItem.from_user(
                    UserDecorator(service).decorate_entity(user_id=user.id, user=u)
                )
                for u in service.get_friends(user.id)
            ]
        }
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
                UserItem.from_user(
                    UserDecorator(service).decorate_entity(user_id=user.id, user=u)
                )
                for u in service.get_incoming_friend_requests(user.id)
            ]
        }
    except Exception as e:
        return exception_response(e)


@social_api.get(
    "/friends/suggestions",
    response_model=UserListEnvelope,
    status_code=200,
)
def get_friend_suggestions(
    service: SocialServiceDependable,
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        suggestions = service.get_friend_suggestions(user.id, limit=limit)
        return {"users": [UserItem.from_user(user) for user in suggestions]}
    except Exception as e:
        return exception_response(e)
