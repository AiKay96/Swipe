from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.core.personal_post.medias import Media
from src.infra.models.personal_post.media import Media as MediaModel


@dataclass
class MediaRepository:
    db: Session

    def create_many(self, medias: list[Media]) -> None:
        db_media = [
            MediaModel(
                post_id=media.post_id,
                url=media.url,
                media_type=media.media_type.value,
            )
            for media in medias
        ]
        self.db.add_all(db_media)
        self.db.commit()
