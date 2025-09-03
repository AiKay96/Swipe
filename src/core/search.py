from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.core.feed import FeedPost
from src.core.users import User


class SearchService(Protocol):
    def search_posts(
        self,
        user_id: UUID,
        query: str,
        *,
        limit: int = 20,
        before: datetime | None = None,
    ) -> list[FeedPost]: ...

    def search_users(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[User]: ...
