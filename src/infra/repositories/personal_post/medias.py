from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError
from src.core.personal_post.medias import Media
from src.infra.models.personal_post.media import Media as MediaModel


@dataclass
class MediaRepository:
    db: Session

    def create(self, media: Media) -> Media:
        db_media = MediaModel(
            post_id=media.post_id,
            url=media.url,
            media_type=media.media_type,
        )
        self.db.add(db_media)
        self.db.commit()
        self.db.refresh(db_media)
        return db_media.to_object()

    def list_by_post(self, post_id: UUID) -> list[Media]:
        return [
            m.to_object()
            for m in self.db.query(MediaModel).filter_by(post_id=post_id).all()
        ]

    def delete(self, media_id: UUID) -> None:
        media = self.db.query(MediaModel).filter_by(id=media_id).first()
        if not media:
            raise DoesNotExistError("Media not found.")
        self.db.delete(media)
        self.db.commit()
