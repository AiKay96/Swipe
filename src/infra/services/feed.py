import random
from dataclasses import dataclass
from datetime import datetime
from math import ceil
from uuid import UUID

from src.core.creator_post.likes import LikeRepository as CreatorPostLikeRepository
from src.core.creator_post.posts import Post as CreatorPost
from src.core.creator_post.posts import PostRepository
from src.core.creator_post.saves import SaveRepository
from src.core.feed import FeedPost, Reaction
from src.core.personal_post.likes import LikeRepository as PersonalPostLikeRepository
from src.core.personal_post.posts import Post as PersonalPost
from src.core.personal_post.posts import PostRepository as PersonalPostRepository
from src.infra.repositories.creator_post.feed_preferences import (
    FeedPreferenceRepository,
)
from src.infra.repositories.creator_post.post_interactions import (
    PostInteractionRepository,
)
from src.infra.repositories.social import FollowRepository, FriendRepository

PER_CATEGORY_HARD_CAP = 12
FETCH_PER_CATEGORY = 40


@dataclass
class FeedService:
    personal_post_repo: PersonalPostRepository
    friend_repo: FriendRepository
    personal_post_like_repo: PersonalPostLikeRepository
    preference_repo: FeedPreferenceRepository
    post_interaction_repo: PostInteractionRepository
    follow_repo: FollowRepository
    post_repo: PostRepository
    save_repo: SaveRepository
    creator_post_like_repo: CreatorPostLikeRepository

    def init_preferences(self, user_id: UUID) -> None:
        self.preference_repo.init_user_preferences(user_id)

    def get_personal_feed(
        self, user_id: UUID, before: datetime, limit: int
    ) -> list[FeedPost]:
        friend_ids = self.friend_repo.get_friend_ids(user_id)
        posts = self.personal_post_repo.get_posts_by_users(friend_ids, before, limit)
        return self._decorate_posts(user_id=user_id, posts=posts, is_creator=False)

    def get_creator_feed_by_category(
        self,
        user_id: UUID,
        category_id: UUID,
        before: datetime,
        limit: int = 20,
    ) -> list[FeedPost]:
        interacted_posts = self.post_interaction_repo.get_recent_interacted_posts(
            user_id
        )
        interacted_post_ids = [p.id for p in interacted_posts]
        followed_user_ids = self.follow_repo.get_following(user_id)
        followed_posts = self.post_repo.get_posts_by_users_in_category(
            user_ids=followed_user_ids,
            category_id=category_id,
            exclude_ids=interacted_post_ids,
            limit=50,
            before=before,
        )
        trending_posts = self.post_repo.get_trending_posts_in_category(
            category_id=category_id,
            exclude_user_ids=followed_user_ids,
            exclude_post_ids=interacted_post_ids,
            limit=30,
        )
        posts = self._mix_category_feed(
            followed=followed_posts,
            trending=trending_posts,
            interacted=interacted_posts,
            limit=limit,
        )

        return self._decorate_posts(
            user_id=user_id,
            posts=posts,
            is_creator=True,
        )

    def _mix_category_feed(
        self,
        followed: list[CreatorPost],
        trending: list[CreatorPost],
        interacted: list[CreatorPost],
        limit: int,
    ) -> list[CreatorPost]:
        result = []

        random.shuffle(followed)
        random.shuffle(trending)
        random.shuffle(interacted)

        num_followed = min(len(followed), int(limit * 0.6))
        result.extend(followed[:num_followed])

        remaining = limit - len(result)
        num_trending = min(len(trending), int(remaining * 0.75))
        result.extend(trending[:num_trending])

        remaining = limit - len(result)
        result.extend(interacted[:remaining])

        random.shuffle(result)
        return result[:limit]

    def get_creator_feed(
        self,
        user_id: UUID,
        before: datetime,
        limit: int = 30,
        top_k_categories: int = 5,
    ) -> list[FeedPost]:
        if limit <= 0:
            return []

        cat_weights: list[tuple[UUID, int]] = (
            self.preference_repo.get_top_categories_with_points(
                user_id=user_id, limit=top_k_categories
            )
        )

        normalized = self._normalize_weights(cat_weights)
        posts: list[FeedPost] = []
        for cid, w in normalized:
            target = ceil(limit * w)

            if target <= 0:
                continue

            fps = self.get_creator_feed_by_category(
                user_id=user_id,
                category_id=cid,
                before=before,
                limit=target,
            )
            posts.extend(fps)

        random.shuffle(posts)
        return posts[:limit]

    def _normalize_weights(
        self, weights: list[tuple[UUID, int]]
    ) -> list[tuple[UUID, float]]:
        if not weights:
            return []

        cleaned = [(cid, points + 1 if points >= 0 else 0) for cid, points in weights]
        total = sum(points for _, points in cleaned)

        if total <= 0:
            return []

        return [(cid, points / total) for cid, points in cleaned]

    def _decorate_posts(
        self,
        user_id: UUID,
        posts: list[PersonalPost] | list[CreatorPost],
        *,
        is_creator: bool,
    ) -> list[FeedPost]:
        if not posts:
            return []

        ids = [p.id for p in posts]

        if is_creator:
            reactions = self.creator_post_like_repo.get_user_reactions(user_id, ids)
            saved_ids = set(self.save_repo.get_user_saves_for_posts(user_id, ids))
        else:
            reactions = self.personal_post_like_repo.get_user_reactions(user_id, ids)

        return [
            FeedPost(
                post=p,
                reaction=reactions.get(p.id, Reaction.NONE),
                is_saved=(p.id in saved_ids if is_creator else None),
            )
            for p in posts
        ]
