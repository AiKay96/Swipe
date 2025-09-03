from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.core.creator_post.posts import (
    Media as CreatorMedia,
)
from src.core.creator_post.posts import (
    MediaType as CreatorMediaType,
)
from src.core.creator_post.posts import (
    Post as CreatorPost,
)
from src.core.feed import FeedPost, Reaction
from src.core.personal_post.posts import (
    Media as PersonalMedia,
)
from src.core.personal_post.posts import (
    MediaType as PersonalMediaType,
)
from src.core.personal_post.posts import Post as PersonalPost
from src.core.personal_post.posts import Privacy


class CreatorMediaItem(BaseModel):
    url: str
    media_type: CreatorMediaType

    @classmethod
    def from_media(cls, media: CreatorMedia) -> "CreatorMediaItem":
        return cls(url=media.url, media_type=media.media_type)


class PersonalMediaItem(BaseModel):
    url: str
    media_type: PersonalMediaType

    @classmethod
    def from_media(cls, media: PersonalMedia) -> "PersonalMediaItem":
        return cls(url=media.url, media_type=media.media_type)


class CreatorPostItem(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    category_id: UUID | None
    category_name: str | None
    reference_id: UUID | None
    reference_title: str | None
    description: str
    like_count: int
    dislike_count: int
    created_at: datetime
    media: list[CreatorMediaItem]

    @classmethod
    def from_post(cls, post: CreatorPost) -> "CreatorPostItem":
        return cls(
            id=post.id,
            user_id=post.user_id,
            username=post.username if post.username else "Unknown",
            category_id=post.category_id,
            category_name=post.category_name,
            reference_id=post.reference_id,
            reference_title=post.reference_title,
            description=post.description,
            like_count=post.like_count,
            dislike_count=post.dislike_count,
            created_at=post.created_at,
            media=[CreatorMediaItem.from_media(m) for m in post.media],
        )


class PersonalPostItem(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    description: str
    privacy: Privacy
    like_count: int
    dislike_count: int
    created_at: datetime
    media: list[PersonalMediaItem]

    @classmethod
    def from_post(cls, post: PersonalPost) -> "PersonalPostItem":
        return cls(
            id=post.id,
            user_id=post.user_id,
            username=post.username if post.username else "Unknown",
            description=post.description,
            privacy=post.privacy,
            like_count=post.like_count,
            dislike_count=post.dislike_count,
            created_at=post.created_at,
            media=[PersonalMediaItem.from_media(m) for m in post.media],
        )


class FeedPostItem(BaseModel):
    post: PersonalPostItem | CreatorPostItem
    is_saved: bool | None = None
    reaction: Reaction

    @classmethod
    def from_post(cls, feed_post: FeedPost) -> "FeedPostItem":
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
