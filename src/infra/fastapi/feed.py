from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.feed import FeedPost, Reaction
from src.core.users import User
from src.infra.fastapi.dependables import FeedServiceDependable, get_current_user
from src.infra.fastapi.utils import exception_response

feed_api = APIRouter(tags=["Feed"])


class FeedPostItem(BaseModel):
    id: UUID
    user_id: UUID
    description: str
    created_at: datetime
    like_count: int
    dislike_count: int
    reaction: Reaction

    @classmethod
    def from_feed_post(cls, feed_post: FeedPost) -> "FeedPostItem":
        post = feed_post.post
        return cls(
            id=post.id,
            user_id=post.user_id,
            description=post.description,
            created_at=post.created_at,
            like_count=post.like_count,
            dislike_count=post.dislike_count,
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
