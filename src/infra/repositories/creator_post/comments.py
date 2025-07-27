from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.creator_post.comments import Comment
from src.core.errors import DoesNotExistError
from src.infra.models.creator_post.comment import (
    Comment as CommentModel,
)


@dataclass
class CommentRepository:
    db: Session

    def create(self, comment: Comment) -> Comment:
        db_comment = CommentModel(
            post_id=comment.post_id,
            user_id=comment.user_id,
            content=comment.content,
        )
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)
        return db_comment.to_object()

    def get(self, comment_id: UUID) -> Comment | None:
        comment = self.db.query(CommentModel).filter_by(id=comment_id).first()
        return comment.to_object() if comment else None

    def delete(self, comment_id: UUID) -> None:
        comment = self.db.query(CommentModel).filter_by(id=comment_id).first()
        if not comment:
            raise DoesNotExistError("Comment not found.")
        self.db.delete(comment)
        self.db.commit()
