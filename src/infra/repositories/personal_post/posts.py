from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError
from src.core.personal_post.posts import Post
from src.infra.models.personal_post.post import Post as PersonalPostModel


@dataclass
class PostRepository:
    db: Session

    def create(self, post: Post) -> Post:
        db_post = PersonalPostModel(
            user_id=post.user_id,
            description=post.description,
            like_count=post.like_count,
            dislike_count=post.dislike_count,
        )
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post.to_object()

    def get(self, post_id: UUID) -> Post | None:
        db_post = self.db.query(PersonalPostModel).filter_by(id=post_id).first()
        return db_post.to_object() if db_post else None

    def update_like_counts(
        self, post_id: UUID, like_count_delta: int = 0, dislike_count_delta: int = 0
    ) -> None:
        post = self.db.query(PersonalPostModel).filter_by(id=post_id).first()
        if not post:
            raise DoesNotExistError("Post not found.")

        post.like_count += like_count_delta
        post.dislike_count += dislike_count_delta
        self.db.commit()

    def delete(self, post_id: UUID) -> None:
        post = self.db.query(PersonalPostModel).filter_by(id=post_id).first()
        if not post:
            raise DoesNotExistError("Post not found.")
        self.db.delete(post)
        self.db.commit()
