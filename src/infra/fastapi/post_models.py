from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.core.creator_post.comments import Comment as CreatorComment
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
from src.core.personal_post.comments import Comment as PersonalComment
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


class CommentItem(BaseModel):
    id: UUID
    post_id: UUID
    user_id: UUID
    username: str
    display_name: str
    content: str
    created_at: datetime
    profile_pic: str | None = None

    @classmethod
    def from_comment(cls, comment: CreatorComment | PersonalComment) -> "CommentItem":
        assert comment.user is not None
        return cls(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user.id,
            display_name=comment.user.display_name,
            username=comment.user.username,
            profile_pic=comment.user.profile_pic,
            content=comment.content,
            created_at=comment.created_at,
        )


class CommentListEnvelope(BaseModel):
    comments: list[CommentItem]


class CreatorPostItem(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    display_name: str
    profile_pic: str | None
    category_id: UUID | None
    category_name: str | None
    reference_id: UUID | None
    reference_title: str | None
    description: str
    like_count: int
    dislike_count: int
    created_at: datetime
    hashtag_names: list[str]
    category_tag_names: list[str]
    media: list[CreatorMediaItem]

    @classmethod
    def from_post(cls, post: CreatorPost) -> "CreatorPostItem":
        assert post.user is not None
        return cls(
            id=post.id,
            user_id=post.user_id,
            username=post.user.username,
            display_name=post.user.display_name,
            profile_pic=post.user.profile_pic,
            category_id=post.category_id,
            category_name=post.category_name,
            reference_id=post.reference_id,
            reference_title=post.reference_title,
            description=post.description,
            like_count=post.like_count,
            dislike_count=post.dislike_count,
            created_at=post.created_at,
            hashtag_names=post.hashtag_names,
            category_tag_names=post.category_tag_names,
            media=[CreatorMediaItem.from_media(m) for m in post.media],
        )


class PersonalPostItem(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    display_name: str
    profile_pic: str | None
    description: str
    privacy: Privacy
    like_count: int
    dislike_count: int
    created_at: datetime
    media: list[PersonalMediaItem]

    @classmethod
    def from_post(cls, post: PersonalPost) -> "PersonalPostItem":
        assert post.user is not None
        return cls(
            id=post.id,
            user_id=post.user_id,
            username=post.user.username,
            display_name=post.user.display_name,
            profile_pic=post.user.profile_pic,
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
