from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from starlette.responses import JSONResponse

from src.core.personal_post.posts import Media, MediaType, Post, Privacy
from src.core.users import User
from src.infra.fastapi.dependables import (
    PersonalPostServiceDependable,
    get_current_user,
)
from src.infra.fastapi.utils import exception_response

personal_post_api = APIRouter(tags=["PersonalPosts"])


class MediaInput(BaseModel):
    url: str
    media_type: MediaType


class CreatePostRequest(BaseModel):
    description: str
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


def extract_post_fields(post: Post) -> dict[str, Any]:
    return {
        "id": post.id,
        "user_id": post.user_id,
        "description": post.description,
        "like_count": post.like_count,
        "dislike_count": post.dislike_count,
        "created_at": post.created_at,
        "media": [MediaItem(url=m.url, media_type=m.media_type) for m in post.media],
    }


class MediaItem(BaseModel):
    url: str
    media_type: MediaType

    @classmethod
    def from_media(cls, media: Media) -> "MediaItem":
        return cls(url=media.url, media_type=media.media_type)


class PostItem(BaseModel):
    id: UUID
    user_id: UUID
    description: str
    privacy: Privacy
    like_count: int
    dislike_count: int
    created_at: datetime
    media: list[MediaItem]

    @classmethod
    def from_post(cls, post: Post) -> "PostItem":
        return cls(
            id=post.id,
            user_id=post.user_id,
            description=post.description,
            privacy=post.privacy,
            like_count=post.like_count,
            dislike_count=post.dislike_count,
            created_at=post.created_at,
            media=[MediaItem.from_media(m) for m in post.media],
        )


class PostEnvelope(BaseModel):
    post: PostItem


class PostListEnvelope(BaseModel):
    posts: list[PostItem]


@personal_post_api.post(
    "/posts",
    status_code=201,
    response_model=PostEnvelope,
)
def create_post(
    request: CreatePostRequest,
    service: PersonalPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        media_objs = [Media(url=m.url, media_type=m.media_type) for m in request.media]
        post = service.create_post(
            user_id=user.id, description=request.description, media=media_objs
        )
        return {"post": PostItem.from_post(post)}
    except Exception as e:
        return exception_response(e)


@personal_post_api.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: UUID,
    service: PersonalPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.delete_post(post_id=post_id, user_id=user.id)
        return JSONResponse(
            status_code=204, content={"message": "Post removed successfully."}
        )
    except Exception as e:
        return exception_response(e)


@personal_post_api.post("/posts/{post_id}/privacy", status_code=200)
def change_post_privacy(
    post_id: UUID,
    service: PersonalPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.change_privacy(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=200, content={"message": "Post privacy updated successfully."}
        )
    except Exception as e:
        return exception_response(e)


@personal_post_api.post("/posts/{post_id}/like", status_code=200)
def like_post(
    post_id: UUID,
    service: PersonalPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.like_post(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=200, content={"message": "Post liked successfully."}
        )
    except Exception as e:
        return exception_response(e)


@personal_post_api.post("/posts/{post_id}/dislike", status_code=200)
def dislike_post(
    post_id: UUID,
    service: PersonalPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.dislike_post(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=200, content={"message": "Post disliked successfully."}
        )
    except Exception as e:
        return exception_response(e)


@personal_post_api.post("/posts/{post_id}/unlike", status_code=200)
def unlike_post(
    post_id: UUID,
    service: PersonalPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.unlike_post(user_id=user.id, post_id=post_id)
        return JSONResponse(
            status_code=200, content={"message": "Reaction removed successfully."}
        )
    except Exception as e:
        return exception_response(e)


@personal_post_api.post("/posts/{post_id}/comments", status_code=201)
def comment_post(
    post_id: UUID,
    request: CommentRequest,
    service: PersonalPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.comment_post(user_id=user.id, post_id=post_id, content=request.content)
        return JSONResponse(
            status_code=201, content={"message": "Comment added successfully."}
        )
    except Exception as e:
        return exception_response(e)


@personal_post_api.delete("/posts/{post_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    service: PersonalPostServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> JSONResponse:
    try:
        service.remove_comment(post_id=post_id, comment_id=comment_id, user_id=user.id)
        return JSONResponse(
            status_code=204, content={"message": "Comment deleted successfully."}
        )
    except Exception as e:
        return exception_response(e)


@personal_post_api.get(
    "/users/{user_id}/personal_posts",
    response_model=PostListEnvelope,
)
def get_user_personal_posts(
    user_id: UUID,
    service: PersonalPostServiceDependable,
    before: datetime | None = None,
    limit: int = Query(15, ge=1, le=50),
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        if before is None:
            before = datetime.now()
        posts = service.get_user_posts(
            user_id=user_id, from_user_id=user.id, limit=limit, before=before
        )
        return {"posts": [PostItem.from_post(p) for p in posts]}
    except Exception as e:
        return exception_response(e)
