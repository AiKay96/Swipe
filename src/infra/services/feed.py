import random
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.core.creator_post.likes import LikeRepository as CreatorPostLikeRepository
from src.core.creator_post.posts import Post, PostRepository
from src.core.creator_post.saves import SaveRepository
from src.core.feed import FeedPost, Reaction
from src.core.personal_post.likes import LikeRepository as PersonalPostLikeRepository
from src.core.personal_post.posts import PostRepository as PersonalPostRepository
from src.infra.repositories.creator_post.feed_preferences import (
    FeedPreferenceRepository,
)
from src.infra.repositories.creator_post.post_interactions import (
    PostInteractionRepository,
)
from src.infra.repositories.social import FollowRepository, FriendRepository


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

    def get_personal_feed(
        self, user_id: UUID, before: datetime, limit: int
    ) -> list[FeedPost]:
        friend_ids = self.friend_repo.get_friend_ids(user_id)
        posts = self.personal_post_repo.get_posts_by_users(friend_ids, before, limit)
        reactions = self.personal_post_like_repo.get_user_reactions(
            user_id, [p.id for p in posts]
        )

        return [
            FeedPost(post=p, reaction=reactions.get(p.id, Reaction.NONE)) for p in posts
        ]

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

        saved_ids = set(
            self.save_repo.get_user_saves_for_posts(user_id, [p.id for p in posts])
        )
        reactions = self.creator_post_like_repo.get_user_reactions(
            user_id, [p.id for p in posts]
        )

        return [
            FeedPost(
                post=p,
                reaction=reactions.get(p.id, Reaction.NONE),
                is_saved=p.id in saved_ids,
            )
            for p in posts
        ]

    def _mix_category_feed(
        self,
        followed: list[Post],
        trending: list[Post],
        interacted: list[Post],
        limit: int,
    ) -> list[Post]:
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
