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
    def init_preferences(self, user_id: UUID) -> None: ...

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


class FeedPreferenceRepository(Protocol):
    def init_user_preferences(self, user_id: UUID) -> None: ...

    def add_points(self, user_id: UUID, category_id: UUID, delta: int) -> None: ...

    def get_top_categories_with_points(
        self, user_id: UUID, limit: int = 5
    ) -> list[tuple[UUID, int]]: ...
