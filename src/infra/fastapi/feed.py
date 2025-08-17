from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.creator_post.posts import Post as CreatorPost
from src.core.feed import FeedPost, Reaction
from src.core.personal_post.posts import Post as PersonalPost
from src.core.users import User
from src.infra.fastapi.creator_posts import (
    PostItem as CreatorPostItem,
)
from src.infra.fastapi.dependables import FeedServiceDependable, get_current_user
from src.infra.fastapi.personal_posts import (
    PostItem as PersonalPostItem,
)
from src.infra.fastapi.utils import exception_response

feed_api = APIRouter(tags=["Feed"])


class FeedPostItem(BaseModel):
    post: PersonalPostItem | CreatorPostItem
    is_saved: bool | None = None
    reaction: Reaction

    @classmethod
    def from_feed_post(cls, feed_post: FeedPost) -> "FeedPostItem":
        p = feed_post.post

        post_item: PersonalPostItem | CreatorPostItem
        if isinstance(p, CreatorPost):
            post_item = CreatorPostItem.from_post(p)
        elif isinstance(p, PersonalPost):
            post_item = PersonalPostItem.from_post(p)
        else:
            raise TypeError(f"Unsupported post type: {type(p)!r}")

        return cls(
            post=post_item,
            is_saved=feed_post.is_saved,
            reaction=feed_post.reaction,
        )


class FeedResponse(BaseModel):
    posts: list[FeedPostItem]


@feed_api.get("/personal_feed", response_model=FeedResponse, status_code=200)
def get_personal_feed(
    service: FeedServiceDependable,
    before: datetime | None = None,
    limit: int = Query(15, ge=1, le=50),
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        if not before:
            before = datetime.now()
        return {
            "posts": [
                FeedPostItem.from_feed_post(u)
                for u in service.get_personal_feed(user.id, before, limit)
            ]
        }
    except Exception as e:
        return exception_response(e)


@feed_api.get("/creator_feed/by_category", response_model=FeedResponse, status_code=200)
def get_creator_feed_by_category(
    service: FeedServiceDependable,
    category_id: UUID,
    before: datetime | None = None,
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        if not before:
            before = datetime.now()
        posts = service.get_creator_feed_by_category(
            user_id=user.id,
            category_id=category_id,
            before=before,
            limit=limit,
        )
        return {"posts": [FeedPostItem.from_feed_post(p) for p in posts]}
    except Exception as e:
        return exception_response(e)


@feed_api.get("/creator_feed", response_model=FeedResponse, status_code=200)
def get_creator_feed(
    service: FeedServiceDependable,
    before: datetime | None = None,
    limit: int = Query(30, ge=1, le=50),
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        if not before:
            before = datetime.now()
        posts = service.get_creator_feed(
            user_id=user.id,
            before=before,
            limit=limit,
        )
        return {"posts": [FeedPostItem.from_feed_post(p) for p in posts]}
    except Exception as e:
        return exception_response(e)
