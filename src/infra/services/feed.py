from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.core.feed import FeedPost, Reaction
from src.core.personal_post.likes import LikeRepository
from src.core.personal_post.posts import PostRepository
from src.infra.repositories.social import FriendRepository


@dataclass
class FeedService:
    post_repo: PostRepository
    friend_repo: FriendRepository
    like_repo: LikeRepository

    def get_personal_feed(
        self, user_id: UUID, before: datetime, limit: int
    ) -> list[FeedPost]:
        friend_ids = self.friend_repo.get_friend_ids(user_id)
        posts = self.post_repo.get_posts_by_users(friend_ids, before, limit)
        reactions = self.like_repo.get_user_reactions(user_id, [p.id for p in posts])

        return [
            FeedPost(post=p, reaction=reactions.get(p.id, Reaction.NONE)) for p in posts
        ]
