from datetime import datetime
from typing import Protocol

from src.core.creator_post.posts import Post as CreatorPost
from src.core.users import User


class SearchService(Protocol):
    def search_posts(
        self,
        query: str,
        *,
        limit: int = 20,
        before: datetime | None = None,
    ) -> list[CreatorPost]: ...

    def search_users(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[User]: ...
