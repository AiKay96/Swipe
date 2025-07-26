from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol
from uuid import UUID

from src.core.personal_post.posts import Post


class Reaction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    NONE = "none"


@dataclass
class FeedPost:
    post: Post
    reaction: Reaction = Reaction.NONE


class FeedService(Protocol):
    def get_personal_feed(
        self, user_id: UUID, before: datetime, limit: int
    ) -> list[FeedPost]: ...
