from __future__ import annotations

import contextlib
import random
from dataclasses import dataclass, field
from datetime import datetime
from math import ceil
from typing import Any
from uuid import UUID

from src.core.creator_post.categories import Category
from src.core.creator_post.posts import Post as CreatorPost
from src.core.creator_post.posts import PostRepository
from src.core.feed import FeedPost
from src.core.personal_post.posts import PostRepository as PersonalPostRepository
from src.infra.decorators.post import PostDecorator
from src.infra.repositories.creator_post.feed_preferences import (
    FeedPreferenceRepository,
)
from src.infra.repositories.creator_post.post_interactions import (
    PostInteractionRepository,
)
from src.infra.repositories.social import FollowRepository, FriendRepository
from src.infra.services.cache import Cache

PER_CATEGORY_HARD_CAP = 12
FETCH_PER_CATEGORY = 40

# TTLs
TTL_CREATOR_IDS_BY_CAT = 120
TTL_CREATOR_IDS_AGG = 180
TTL_POST_OBJ = 90
TTL_FOLLOW_IDS = 180
TTL_TOPCATS = 420


def _minute_bucket(dt: datetime) -> str:
    return dt.replace(second=0, microsecond=0).isoformat(timespec="minutes")


@dataclass
class FeedService:
    personal_post_repo: PersonalPostRepository
    friend_repo: FriendRepository
    preference_repo: FeedPreferenceRepository
    post_interaction_repo: PostInteractionRepository
    follow_repo: FollowRepository
    post_repo: PostRepository
    post_decorator: PostDecorator
    _cache: Cache = field(default_factory=Cache)

    def init_preferences(self, user_id: UUID) -> None:
        self.preference_repo.init_user_preferences(user_id)

    def get_personal_feed(
        self, user_id: UUID, before: datetime, limit: int
    ) -> list[FeedPost]:
        friend_ids = self.friend_repo.get_friend_ids(user_id)
        posts = self.personal_post_repo.get_posts_by_users(friend_ids, before, limit)
        return self.post_decorator.decorate_list(
            user_id=user_id, posts=posts, is_creator=False
        )

    def get_creator_feed_by_category(
        self,
        user_id: UUID,
        category_id: UUID,
        before: datetime,
        limit: int = 20,
    ) -> list[FeedPost]:
        if limit <= 0:
            return []

        user_cache = self._user_cache(user_id)
        ids_key = self._key_creator_ids_by_cat(user_id, category_id, before, limit)

        raw_ids = self._cget(user_cache, ids_key)
        cached_ids = self._coerce_uuid_list(raw_ids)
        if cached_ids:
            posts = self._batch_get_creator_posts_with_cache(cached_ids)
            return self.post_decorator.decorate_list(
                user_id=user_id, posts=posts, is_creator=True
            )

        interacted_posts = self.post_interaction_repo.get_recent_interacted_posts(
            user_id
        )
        interacted_post_ids = [p.id for p in interacted_posts]

        followed_user_ids = self._cached_follow_ids(user_id)

        followed_posts = self.post_repo.get_posts_by_users_in_category(
            user_ids=followed_user_ids,
            category_id=category_id,
            exclude_ids=interacted_post_ids,
            limit=50,
            before=before,
        )

        exclude_user_ids = list(followed_user_ids)
        exclude_user_ids.append(user_id)

        trending_posts = self.post_repo.get_trending_posts_in_category(
            category_id=category_id,
            exclude_user_ids=exclude_user_ids,
            exclude_post_ids=interacted_post_ids,
            limit=30,
        )

        posts = self._mix_category_feed(
            followed=followed_posts,
            trending=trending_posts,
            interacted=interacted_posts,
            limit=limit,
        )

        self._cset(
            user_cache, ids_key, [str(p.id) for p in posts], TTL_CREATOR_IDS_BY_CAT
        )

        for p in posts:
            self._cset(self._cache, self._key_post_obj(p.id), p, TTL_POST_OBJ)

        return self.post_decorator.decorate_list(
            user_id=user_id, posts=posts, is_creator=True
        )

    def get_creator_feed(
        self,
        user_id: UUID,
        before: datetime,
        limit: int = 30,
        top_k_categories: int = 25,
    ) -> list[FeedPost]:
        if limit <= 0:
            return []

        user_cache = self._user_cache(user_id)
        agg_key = self._key_creator_ids_agg(user_id, before, limit, top_k_categories)

        raw_ids = self._cget(user_cache, agg_key)
        cached_ids = self._coerce_uuid_list(raw_ids)
        if cached_ids:
            posts = self._batch_get_creator_posts_with_cache(cached_ids)
            random.shuffle(posts)
            return self.post_decorator.decorate_list(
                user_id=user_id, posts=posts[:limit], is_creator=True
            )

        cat_weights = self._cached_top_categories(user_id, top_k_categories)
        normalized = self._normalize_weights(cat_weights)
        if not normalized:
            return []

        all_feedposts: list[FeedPost] = []
        all_ids: list[UUID] = []

        for cid, weight in normalized:
            target = ceil(limit * weight)
            if target <= 0:
                continue
            chunk = self.get_creator_feed_by_category(
                user_id=user_id,
                category_id=cid,
                before=before,
                limit=target,
            )
            all_feedposts.extend(chunk)
            all_ids.extend([fp.post.id for fp in chunk])

        for fp in all_feedposts:
            self._cset(
                self._cache, self._key_post_obj(fp.post.id), fp.post, TTL_POST_OBJ
            )

        self._cset(
            user_cache, agg_key, [str(pid) for pid in all_ids], TTL_CREATOR_IDS_AGG
        )

        random.shuffle(all_feedposts)
        return all_feedposts[:limit]

    def get_top_categories(self, user_id: UUID, limit: int = 7) -> list[Category]:
        return self.preference_repo.get_top_categories(user_id=user_id, limit=limit)

    def _mix_category_feed(
        self,
        followed: list[CreatorPost],
        trending: list[CreatorPost],
        interacted: list[CreatorPost],
        limit: int,
    ) -> list[CreatorPost]:
        random.shuffle(followed)
        random.shuffle(trending)
        random.shuffle(interacted)

        result: list[CreatorPost] = []

        num_followed = min(len(followed), int(limit * 0.6))
        result.extend(followed[:num_followed])

        remaining = limit - len(result)
        num_trending = min(len(trending), int(remaining * 0.75))
        result.extend(trending[:num_trending])

        remaining = limit - len(result)
        if remaining > 0:
            result.extend(interacted[:remaining])

        random.shuffle(result)
        return result[:limit]

    def _normalize_weights(
        self, weights: list[tuple[UUID, int]]
    ) -> list[tuple[UUID, float]]:
        if not weights:
            return []
        cleaned = [(cid, (points if points >= 0 else 0) + 1) for cid, points in weights]
        total = sum(points for _, points in cleaned)
        if total <= 0:
            return []
        return [(cid, points / total) for cid, points in cleaned]

    def _key_creator_ids_by_cat(
        self, user_id: UUID, category_id: UUID, before: datetime, limit: int
    ) -> str:
        return (
            f"creator_ids_by_cat:{user_id}:{category_id}:"
            f"{_minute_bucket(before)}:limit{limit}"
        )

    def _key_creator_ids_agg(
        self, user_id: UUID, before: datetime, limit: int, topk: int
    ) -> str:
        return (
            f"creator_ids_agg:{user_id}:{_minute_bucket(before)}:"
            f"limit{limit}:topk{topk}"
        )

    def _key_post_obj(self, post_id: UUID) -> str:
        return f"post_obj:{post_id}"

    def _key_follow_ids(self, user_id: UUID) -> str:
        return f"follow_ids:{user_id}"

    def _key_topcats(self, user_id: UUID, k: int) -> str:
        return f"topcats:{user_id}:k{k}"

    def _cached_follow_ids(self, user_id: UUID) -> list[UUID]:
        user_cache = self._user_cache(user_id)
        key = self._key_follow_ids(user_id)

        raw = self._cget(user_cache, key)
        ids = self._coerce_uuid_list(raw)
        if ids is not None:
            return ids

        followed_user_ids = self.follow_repo.get_following(user_id)
        self._cset(
            user_cache, key, [str(uid) for uid in followed_user_ids], TTL_FOLLOW_IDS
        )
        return followed_user_ids

    def _cached_top_categories(self, user_id: UUID, k: int) -> list[tuple[UUID, int]]:
        user_cache = self._user_cache(user_id)
        key = self._key_topcats(user_id, k)

        raw = self._cget(user_cache, key)
        rows = self._coerce_uuid_int_tuples(raw)
        if rows is not None:
            return rows

        db_rows = self.preference_repo.get_top_categories_with_points(
            user_id=user_id, limit=k
        )
        self._cset(
            user_cache,
            key,
            [(str(cid), int(points)) for cid, points in db_rows],
            TTL_TOPCATS,
        )
        return db_rows

    def _batch_get_creator_posts_with_cache(self, ids: list[UUID]) -> list[CreatorPost]:
        if not ids:
            return []

        keys = [self._key_post_obj(pid) for pid in ids]
        cached_objs = self._cget_many(self._cache, keys)

        found: dict[UUID, CreatorPost] = {}
        missing: list[UUID] = []

        for pid, obj in zip(ids, cached_objs, strict=False):
            if obj is None:
                missing.append(pid)
            else:
                found[pid] = obj

        if missing:
            fetched = self.post_repo.batch_get(missing)
            for p in fetched:
                found[p.id] = p
                self._cset(self._cache, self._key_post_obj(p.id), p, TTL_POST_OBJ)

        return [found[pid] for pid in ids if pid in found]

    def _user_cache(self, user_id: UUID) -> Cache:
        return self._cache.user(str(user_id))

    def _cget(self, cache: Cache, key: str) -> Any | None:
        try:
            return cache.get(key)
        except Exception:
            return None

    def _cset(self, cache: Cache, key: str, value: Any, ttl: int) -> None:
        try:
            cache.set(key, value, ttl)
        except Exception:
            contextlib.suppress(Exception)

    def _cget_many(self, cache: Cache, keys: list[str]) -> list[Any | None]:
        try:
            return [self._cget(cache, k) for k in keys]
        except Exception:
            return [None] * len(keys)

    def _coerce_uuid_list(self, v: Any) -> list[UUID] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            return None
        out: list[UUID] = []
        for x in v:
            if isinstance(x, UUID):
                out.append(x)
            else:
                try:
                    out.append(UUID(str(x)))
                except Exception:
                    return None
        return out

    def _coerce_uuid_int_tuples(self, v: Any) -> list[tuple[UUID, int]] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            return None
        out: list[tuple[UUID, int]] = []
        for item in v:
            if not (isinstance(item, (list | tuple)) and len(item) == 2):
                return None
            cid_raw, points_raw = item
            try:
                cid = cid_raw if isinstance(cid_raw, UUID) else UUID(str(cid_raw))
                points = int(points_raw)
            except Exception:
                return None
            out.append((cid, points))
        return out
