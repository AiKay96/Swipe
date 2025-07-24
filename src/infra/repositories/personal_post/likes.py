from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError
from src.core.personal_post.personal_post_like import PersonalPostLike
from src.infra.models.personal_post.like import Like as PersonalPostLikeModel


@dataclass
class LikeRepository:
    db: Session

    def create(self, like: PersonalPostLike) -> PersonalPostLike:
        db_like = PersonalPostLikeModel(
            post_id=like.post_id,
            user_id=like.user_id,
            is_dislike=like.is_dislike,
        )
        self.db.add(db_like)
        self.db.commit()
        self.db.refresh(db_like)
        return db_like.to_object()

    def get_by_user_and_post(
        self, user_id: UUID, post_id: UUID
    ) -> PersonalPostLike | None:
        db_like = (
            self.db.query(PersonalPostLikeModel)
            .filter_by(user_id=user_id, post_id=post_id)
            .first()
        )
        return db_like.to_object() if db_like else None

    def update(self, like_id: UUID, is_dislike: bool) -> None:
        db_like = self.db.query(PersonalPostLikeModel).filter_by(id=like_id).first()
        if not db_like:
            raise DoesNotExistError("Like not found.")
        db_like.is_dislike = is_dislike
        self.db.commit()
        self.db.refresh(db_like)

    def delete(self, like_id: UUID) -> None:
        like = self.db.query(PersonalPostLikeModel).filter_by(id=like_id).first()
        if not like:
            raise DoesNotExistError("Like not found.")
        self.db.delete(like)
        self.db.commit()
