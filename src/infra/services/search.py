from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.core.feed import FeedPost
from src.core.users import User
from src.infra.decorators.post import PostDecorator
from src.infra.repositories.creator_post.posts import PostRepository
from src.infra.repositories.users import UserRepository
from src.infra.services.cache import Cache


@dataclass
class SearchService:
    post_repo: PostRepository
    user_repo: UserRepository
    post_decorator: PostDecorator
    _cache: Cache = Cache()

    _ttl_search: int = 60

    def search_posts(
        self,
        user_id: UUID,
        query: str,
        *,
        limit: int = 20,
        before: datetime | None = None,
    ) -> list[FeedPost]:
        key = (
            f"search_posts:{query}:limit{limit}:"
            f"{before.isoformat() if before else 'none'}"
        )
        cached = self._cache.get(key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        posts = self.post_repo.search(query, limit=limit, before=before)
        self._cache.set(key, posts, self._ttl_search)
        return self.post_decorator.decorate_list(
            user_id=user_id, posts=posts, is_creator=True
        )

    def search_users(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[User]:
        key = f"search_users:{query}:limit{limit}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        users = self.user_repo.search(query, limit=limit)
        self._cache.set(key, users, self._ttl_search)
        return users
