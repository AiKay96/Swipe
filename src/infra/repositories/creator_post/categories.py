from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.core.creator_post.categories import (
    Category as DomainCategory,
)
from src.infra.models.creator_post.category import Category as CategoryModel
from src.infra.models.creator_post.category_tag import CategoryTag as CategoryTagModel


@dataclass
class CategoryRepository:
    db: Session

    def create_many(self, categories: list[DomainCategory]) -> None:
        for domain_cat in categories:
            db_cat = CategoryModel(name=domain_cat.name)
            self.db.add(db_cat)
            self.db.flush()

            for domain_tag in domain_cat.tag_names:
                db_tag = CategoryTagModel(
                    category_id=db_cat.id,
                    name=domain_tag,
                )
                self.db.add(db_tag)

        self.db.commit()
