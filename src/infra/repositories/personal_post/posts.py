from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError
from src.core.personal_post.posts import Post, Privacy
from src.infra.models.personal_post.media import Media as MediaModel
from src.infra.models.personal_post.post import Post as PostModel


@dataclass
class PostRepository:
    db: Session

    def create(self, post: Post) -> Post:
        db_post = PostModel(
            user_id=post.user_id,
            description=post.description,
            like_count=post.like_count,
            dislike_count=post.dislike_count,
        )
        self.db.add(db_post)
        self.db.flush()
        db_post.media = [
            MediaModel(post_id=db_post.id, url=m.url, media_type=m.media_type.value)
            for m in post.media
        ]
        self.db.commit()
        self.db.refresh(db_post)
        return db_post.to_object()

    def get(self, post_id: UUID) -> Post | None:
        db_post = self.db.query(PostModel).filter_by(id=post_id).first()
        return db_post.to_object() if db_post else None

    def get_posts_by_user(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
        include_friends_only: bool = False,
    ) -> list[Post]:
        query = self.db.query(PostModel).filter_by(user_id=user_id)

        if before:
            query = query.filter(PostModel.created_at < before)

        if include_friends_only:
            query = query.filter(
                PostModel.privacy.in_(
                    [Privacy.PUBLIC.value, Privacy.FRIENDS_ONLY.value]
                )
            )
        else:
            query = query.filter(PostModel.privacy == Privacy.PUBLIC.value)

        query = query.order_by(PostModel.created_at.desc()).limit(limit)

        return [p.to_object() for p in query.all()]

    def get_posts_by_users(
        self, user_ids: list[UUID], before: datetime, limit: int
    ) -> list[Post]:
        if not user_ids:
            return []

        posts = (
            self.db.query(PostModel)
            .filter(
                PostModel.user_id.in_(user_ids),
                PostModel.created_at < before,
            )
            .order_by(PostModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [p.to_object() for p in posts]

    def update_like_counts(
        self, post_id: UUID, like_count_delta: int = 0, dislike_count_delta: int = 0
    ) -> None:
        post = self.db.query(PostModel).filter_by(id=post_id).first()
        if not post:
            raise DoesNotExistError("Post not found.")

        post.like_count += like_count_delta
        post.dislike_count += dislike_count_delta
        self.db.commit()

    def update_privacy(self, post_id: UUID, privacy: Privacy) -> None:
        post = self.db.query(PostModel).filter_by(id=post_id).first()
        if not post:
            raise DoesNotExistError("Post not found.")
        post.privacy = privacy.value
        self.db.commit()

    def delete(self, post_id: UUID) -> None:
        post = self.db.query(PostModel).filter_by(id=post_id).first()
        if not post:
            raise DoesNotExistError("Post not found.")
        self.db.delete(post)
        self.db.commit()
