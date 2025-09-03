from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.users import User
from src.infra.fastapi.dependables import (
    SearchServiceDependable,
    SocialServiceDependable,
    get_current_user,
)
from src.infra.fastapi.post_models import FeedPostItem
from src.infra.fastapi.users import UserItem
from src.infra.fastapi.utils import exception_response

search_api = APIRouter(tags=["Search"])


class SearchPostsResponse(BaseModel):
    feed_posts: list[FeedPostItem]


class SearchUsersResponse(BaseModel):
    users: list[UserItem]


@search_api.get("/search/posts", response_model=SearchPostsResponse)
def search_posts(
    service: SearchServiceDependable,
    query: str,
    limit: int = Query(20, ge=1, le=50),
    before: datetime | None = None,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        posts = service.search_posts(
            user_id=user.id, query=query, limit=limit, before=before
        )
        return {"feed_posts": [FeedPostItem.from_post(p) for p in posts]}
    except Exception as e:
        return exception_response(e)


@search_api.get("/search/users", response_model=SearchUsersResponse)
def search_users(
    query: str,
    service: SearchServiceDependable,
    social: SocialServiceDependable,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        found = service.search_users(query, limit=limit)
        result = []
        for u in found:
            friend_status = social.get_friend_status(current_user.id, u.id)
            is_following = social.is_following(current_user.id, u.id)
            result.append(UserItem.from_user(u, friend_status, is_following))
        return {"users": result}
    except Exception as e:
        return exception_response(e)
