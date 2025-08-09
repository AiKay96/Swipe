from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID

from src.core.creator_post.posts import Post as CreatorPost
from src.core.personal_post.posts import Post as PersonalPost


class Reaction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    NONE = "none"


@dataclass
class FeedPost:
    post: PersonalPost | CreatorPost
    reaction: Reaction = Reaction.NONE
    is_saved: bool | None = None


class FeedService(Protocol):
    def get_personal_feed(
        self, user_id: UUID, before: datetime, limit: int
    ) -> list[FeedPost]: ...

    def get_creator_feed(
        self, user_id: UUID, before: datetime, limit: int
    ) -> list[FeedPost]: ...

    def get_creator_feed_by_category(
        self,
        user_id: UUID,
        category_id: UUID,
        before: datetime,
        limit: int = 20,
    ) -> list[FeedPost]: ...
