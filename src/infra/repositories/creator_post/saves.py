from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.creator_post.saves import Save
from src.core.errors import DoesNotExistError
from src.infra.models.creator_post.save import Save as SaveModel


@dataclass
class SaveRepository:
    db: Session

    def create(self, save: Save) -> Save:
        db_save = SaveModel(
            post_id=save.post_id,
            user_id=save.user_id,
        )
        self.db.add(db_save)
        self.db.commit()
        self.db.refresh(db_save)
        return db_save.to_object()

    def get(self, user_id: UUID, post_id: UUID) -> Save | None:
        db_save = (
            self.db.query(SaveModel).filter_by(user_id=user_id, post_id=post_id).first()
        )
        return db_save.to_object() if db_save else None

    def delete(self, save_id: UUID) -> None:
        save = self.db.query(SaveModel).filter_by(id=save_id).first()
        if not save:
            raise DoesNotExistError("Save not found.")
        self.db.delete(save)
        self.db.commit()

    def get_user_saves_for_posts(
        self, user_id: UUID, post_ids: list[UUID]
    ) -> list[UUID]:
        saves = (
            self.db.query(SaveModel)
            .filter(SaveModel.user_id == user_id, SaveModel.post_id.in_(post_ids))
            .all()
        )

        return [row.post_id for row in saves]
