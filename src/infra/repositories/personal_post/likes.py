from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError
from src.core.feed import Reaction
from src.core.personal_post.likes import Like
from src.infra.models.personal_post.like import PersonalLike as LikeModel


@dataclass
class LikeRepository:
    db: Session

    def create(self, like: Like) -> Like:
        db_like = LikeModel(
            post_id=like.post_id,
            user_id=like.user_id,
            is_dislike=like.is_dislike,
        )
        self.db.add(db_like)
        self.db.commit()
        self.db.refresh(db_like)
        return db_like.to_object()

    def get(self, user_id: UUID, post_id: UUID) -> Like | None:
        db_like = (
            self.db.query(LikeModel).filter_by(user_id=user_id, post_id=post_id).first()
        )
        return db_like.to_object() if db_like else None

    def update(self, like_id: UUID, is_dislike: bool) -> None:
        db_like = self.db.query(LikeModel).filter_by(id=like_id).first()
        if not db_like:
            raise DoesNotExistError("Like not found.")
        db_like.is_dislike = is_dislike
        self.db.commit()
        self.db.refresh(db_like)

    def delete(self, like_id: UUID) -> None:
        like = self.db.query(LikeModel).filter_by(id=like_id).first()
        if not like:
            raise DoesNotExistError("Like not found.")
        self.db.delete(like)
        self.db.commit()

    def get_user_reactions(
        self, user_id: UUID, post_ids: list[UUID]
    ) -> dict[UUID, Reaction]:
        likes = (
            self.db.query(LikeModel)
            .filter(LikeModel.user_id == user_id, LikeModel.post_id.in_(post_ids))
            .all()
        )

        return {
            like.post_id: Reaction.DISLIKE if like.is_dislike else Reaction.LIKE
            for like in likes
        }
