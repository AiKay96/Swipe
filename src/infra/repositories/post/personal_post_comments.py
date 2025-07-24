from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError
from src.core.post.personal_post_comments import PersonalPostComment
from src.infra.models.post.post_comment import (
    PostPersonalPostComment as PersonalPostCommentModel,
)


@dataclass
class PersonalPostCommentRepository:
    db: Session

    def create(self, comment: PersonalPostComment) -> PersonalPostComment:
        db_comment = PersonalPostCommentModel(
            post_id=comment.post_id,
            user_id=comment.user_id,
            content=comment.content,
        )
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)
        return db_comment.to_object()

    def get_by_post(self, post_id: UUID) -> list[PersonalPostComment]:
        comments = (
            self.db.query(PersonalPostCommentModel).filter_by(post_id=post_id).all()
        )
        return [c.to_object() for c in comments]

    def delete(self, comment_id: UUID) -> None:
        comment = (
            self.db.query(PersonalPostCommentModel).filter_by(id=comment_id).first()
        )
        if not comment:
            raise DoesNotExistError("PersonalPostComment not found.")
        self.db.delete(comment)
        self.db.commit()
