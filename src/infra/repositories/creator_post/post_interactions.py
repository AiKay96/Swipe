from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.creator_post.posts import Post as DomainPost
from src.infra.models.creator_post.post import Post as CreatorPost
from src.infra.models.creator_post.post_interaction import PostInteraction


@dataclass
class PostInteractionRepository:
    db: Session

    def create_or_update(self, user_id: UUID, post_id: UUID) -> None:
        interaction = (
            self.db.query(PostInteraction)
            .filter_by(user_id=user_id, post_id=post_id)
            .first()
        )
        if not interaction:
            interaction = PostInteraction(user_id=user_id, post_id=post_id)
            self.db.add(interaction)

        self.db.commit()

    def get_recent_interacted_posts(
        self, user_id: UUID, days: int = 30
    ) -> list[DomainPost]:
        cutoff = datetime.now() - timedelta(days=days)
        posts = (
            self.db.query(CreatorPost)
            .join(PostInteraction, CreatorPost.id == PostInteraction.post_id)
            .filter(
                PostInteraction.user_id == user_id,
                PostInteraction.last_interacted_at > cutoff,
            )
            .order_by(PostInteraction.last_interacted_at.desc())
            .all()
        )
        return [p.to_object() for p in posts]
