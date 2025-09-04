from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.users import User
from src.infra.fastapi.dependables import FeedServiceDependable, get_current_user
from src.infra.fastapi.post_models import FeedPostItem
from src.infra.fastapi.references import CategoryItem
from src.infra.fastapi.utils import exception_response

feed_api = APIRouter(tags=["Feed"])


class FeedResponse(BaseModel):
    posts: list[FeedPostItem]


class CategoryListEnvelope(BaseModel):
    categories: list[CategoryItem]


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
                FeedPostItem.from_post(u)
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
        return {"posts": [FeedPostItem.from_post(p) for p in posts]}
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
        return {"posts": [FeedPostItem.from_post(p) for p in posts]}
    except Exception as e:
        return exception_response(e)


@feed_api.get(
    "/creator_feed/top_categories", response_model=CategoryListEnvelope, status_code=200
)
def get_top_categories(
    service: FeedServiceDependable,
    limit: int = Query(7, ge=1, le=50),
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        cats = service.get_top_categories(user_id=user.id, limit=limit)
        return {"categories": [CategoryItem.from_category(c) for c in cats]}
    except Exception as e:
        return exception_response(e)
