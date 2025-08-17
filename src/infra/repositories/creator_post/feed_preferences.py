from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.infra.models.creator_post.category import Category as CategoryModel
from src.infra.models.creator_post.feed_preference import FeedPreference


@dataclass
class FeedPreferenceRepository:
    db: Session

    def init_user_preferences(self, user_id: UUID) -> None:
        category_ids = [cid for (cid,) in self.db.query(CategoryModel.id).all()]
        if not category_ids:
            return

        self.db.add_all(
            [
                FeedPreference(user_id=user_id, category_id=cid, points=0)
                for cid in category_ids
            ]
        )
        self.db.commit()

    def add_points(self, user_id: UUID, category_id: UUID, delta: int) -> None:
        pref = (
            self.db.query(FeedPreference)
            .filter_by(user_id=user_id, category_id=category_id)
            .first()
        )
        if pref:
            pref.points += delta
        else:
            pref = FeedPreference(
                user_id=user_id, category_id=category_id, points=delta
            )
            self.db.add(pref)
        self.db.commit()

    def get_top_categories_with_points(
        self, user_id: UUID, limit: int = 5
    ) -> list[tuple[UUID, int]]:
        rows = (
            self.db.query(FeedPreference.category_id, FeedPreference.points)
            .filter_by(user_id=user_id)
            .order_by(FeedPreference.points.desc())
            .limit(limit)
            .all()
        )

        return [(cid, int(points)) for (cid, points) in rows]
