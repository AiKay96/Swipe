from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from starlette.responses import JSONResponse

from src.core.errors import DoesNotExistError, ExistsError
from src.core.personal_post.posts import Media, MediaType, Post
from src.core.users import User
from src.infra.fastapi.dependables import (
    PersonalPostServiceDependable,
    get_current_user,
)

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
        "media": [
            MediaResponse(url=m.url, media_type=m.media_type) for m in post.media
        ],
    }


class MediaResponse(BaseModel):
    url: str
    media_type: MediaType


class PostResponse(BaseModel):
    id: UUID
    user_id: UUID
    description: str
    like_count: int
    dislike_count: int
    created_at: datetime
    media: list[MediaResponse]


class PostEnvelope(BaseModel):
    post: PostResponse


def exception_response(e: Exception) -> JSONResponse:
    if isinstance(e, DoesNotExistError):
        return JSONResponse(status_code=404, content={"message": "Resource not found."})
    if isinstance(e, ExistsError):
        return JSONResponse(
            status_code=409, content={"message": "Conflict: Already exists."}
        )
    return JSONResponse(status_code=500, content={"message": str(e)})


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
        return {"post": extract_post_fields(post)}
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
