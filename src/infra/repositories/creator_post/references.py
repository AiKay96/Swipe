from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.creator_post.references import Reference as DomainReference
from src.infra.models.creator_post.category_tag import CategoryTag as CategoryTagModel
from src.infra.models.creator_post.reference import Reference as ReferenceModel


@dataclass
class ReferenceRepository:
    db: Session

    def create_many(
        self,
        category_id: UUID,
        references: list[DomainReference],
    ) -> None:
        all_tag_names = {tag for ref in references for tag in ref.tag_names}
        tag_map = {
            tag.name: tag
            for tag in self.db.query(CategoryTagModel)
            .filter(
                CategoryTagModel.name.in_(all_tag_names),
                CategoryTagModel.category_id == category_id,
            )
            .all()
        }

        for ref in references:
            db_ref = ReferenceModel(
                category_id=category_id,
                title=ref.title,
                description=ref.description,
                image_url=ref.image_url,
                attributes=ref.attributes,
            )
            self.db.add(db_ref)
            self.db.flush()

            db_ref.tags.extend(
                [tag_map[name] for name in ref.tag_names if name in tag_map]
            )

        self.db.commit()
