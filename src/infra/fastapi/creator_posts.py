from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from starlette.responses import JSONResponse

from src.core.creator_post.posts import Media, MediaType
from src.core.users import User
from src.infra.fastapi.dependables import (
    CreatorPostServiceDependable,
    get_current_user,
)
from src.infra.fastapi.post_models import CommentItem, FeedPostItem
from src.infra.fastapi.utils import exception_response

creator_post_api = APIRouter(tags=["CreatorPosts"])


class MediaInput(BaseModel):
    url: str
    media_type: MediaType


class CreatePostRequest(BaseModel):
    category_id: UUID
    reference_id: UUID | None
    description: str
    category_tag_names: list[str]
    hashtag_names: list[str]
    media: list[MediaInput]

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 2048:
            raise ValueError("Description too long")
        return v

    @field_validator("media")
    @classmethod
    def validate_media(cls, v: list[MediaInput]) -> list[MediaInput]:
        if len(v) > 10:
            raise ValueError("Too many media items")
        return v


class CommentRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Comment too short")
        if len(v) > 1000:
            raise ValueError("Comment too long")
        return v


class CommentListEnvelope(BaseModel):
    comments: list[CommentItem]


class PostEnvelope(BaseModel):
    feed_post: FeedPostItem


class PostListEnvelope(BaseModel):
    feed_posts: list[FeedPostItem]


@creator_post_api.post("/creator-posts", status_code=201, response_model=PostEnvelope)
def create_post(
    request: CreatePostRequest,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        media_objs = [Media(url=m.url, media_type=m.media_type) for m in request.media]
        post = service.create_post(
            user_id=user.id,
            category_id=request.category_id,
            reference_id=request.reference_id,
            description=request.description,
            category_tag_names=request.category_tag_names,
            hashtag_names=request.hashtag_names,
            media=media_objs,
        )
        return {"feed_post": FeedPostItem.from_post(post)}
    except Exception as e:
        return exception_response(e)


@creator_post_api.delete("/creator-posts/{post_id}", status_code=204)
def delete_post(
    post_id: UUID,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.delete_post(post_id=post_id, user_id=user.id)
        return JSONResponse(
            status_code=204, content={"message": "Post removed successfully."}
        )
    except Exception as e:
        return exception_response(e)


@creator_post_api.post("/creator-posts/{post_id}/like", status_code=200)
def like_post(
    post_id: UUID,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.like_post(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=200, content={"message": "Post liked successfully."}
        )
    except Exception as e:
        return exception_response(e)


@creator_post_api.post("/creator-posts/{post_id}/dislike", status_code=200)
def dislike_post(
    post_id: UUID,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.dislike_post(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=200, content={"message": "Post disliked successfully."}
        )
    except Exception as e:
        return exception_response(e)


@creator_post_api.post("/creator-posts/{post_id}/unlike", status_code=200)
def unlike_post(
    post_id: UUID,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.unlike_post(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=200, content={"message": "Reaction removed successfully."}
        )
    except Exception as e:
        return exception_response(e)


@creator_post_api.post("/creator-posts/{post_id}/save", status_code=200)
def save_post(
    post_id: UUID,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.save_post(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=200, content={"message": "Post saved successfully."}
        )
    except Exception as e:
        return exception_response(e)


@creator_post_api.delete("/creator-posts/{post_id}/save", status_code=204)
def remove_save(
    post_id: UUID,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.remove_save(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=204, content={"message": "Save removed successfully."}
        )
    except Exception as e:
        return exception_response(e)


@creator_post_api.get(
    "/creator-posts/{post_id}/comments",
    status_code=200,
    response_model=CommentListEnvelope,
)
def list_post_comments(
    post_id: UUID,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008, ARG001
) -> dict[str, Any] | JSONResponse:
    try:
        comments = service.get_comments_by_post(post_id)
        return {"comments": [CommentItem.from_comment(c) for c in comments]}
    except Exception as e:
        return exception_response(e)


@creator_post_api.post("/creator-posts/{post_id}/comments", status_code=201)
def comment_post(
    post_id: UUID,
    request: CommentRequest,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.comment_post(user_id=user.id, post_id=post_id, content=request.content)
        return JSONResponse(
            status_code=201, content={"message": "Comment added successfully."}
        )
    except Exception as e:
        return exception_response(e)


@creator_post_api.delete(
    "/creator-posts/{post_id}/comments/{comment_id}", status_code=204
)
def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    service: CreatorPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.remove_comment(post_id=post_id, comment_id=comment_id, user_id=user.id)
        return JSONResponse(
            status_code=204, content={"message": "Comment deleted successfully."}
        )
    except Exception as e:
        return exception_response(e)


@creator_post_api.get(
    "/users/{user_id}/creator_posts",
    response_model=PostListEnvelope,
)
def get_user_creator_posts(
    user_id: UUID,
    service: CreatorPostServiceDependable,
    before: datetime | None = None,
    limit: int = Query(15, ge=1, le=50),
    user: User = Depends(get_current_user),  # noqa: B008, ARG001
) -> dict[str, Any] | JSONResponse:
    try:
        if before is None:
            before = datetime.now()
        posts = service.get_user_posts(user_id=user_id, limit=limit, before=before)
        return {"feed_posts": [FeedPostItem.from_post(p) for p in posts]}
    except Exception as e:
        return exception_response(e)


@creator_post_api.get(
    "/creator-posts/saves",
    response_model=PostListEnvelope,
)
def get_my_saved_posts(
    service: CreatorPostServiceDependable,
    before: datetime | None = None,
    limit: int = Query(15, ge=1, le=50),
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        if before is None:
            before = datetime.now()
        posts = service.get_user_saves(user_id=user.id, limit=limit, before=before)
        return {"feed_posts": [FeedPostItem.from_post(p) for p in posts]}
    except Exception as e:
        return exception_response(e)
