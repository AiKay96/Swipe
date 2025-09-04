from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from src.core.creator_post.categories import Category
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
                FeedPreference(user_id=user_id, category_id=cid, points=1)
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

    def get_top_categories(self, user_id: UUID, limit: int = 7) -> list[Category]:
        rows = (
            self.db.query(CategoryModel, FeedPreference.points)
            .join(FeedPreference, FeedPreference.category_id == CategoryModel.id)
            .filter(FeedPreference.user_id == user_id)
            .order_by(FeedPreference.points.desc(), CategoryModel.name.asc())
            .limit(limit)
            .all()
        )
        if rows:
            return [(cm.to_object()) for (cm, _) in rows]

        agg_rows = (
            self.db.query(
                CategoryModel,
                func.coalesce(func.sum(FeedPreference.points), 0).label("score"),
            )
            .outerjoin(FeedPreference, FeedPreference.category_id == CategoryModel.id)
            .group_by(CategoryModel.id)
            .order_by(desc("score"), asc(CategoryModel.name))
            .limit(limit)
            .all()
        )
        if agg_rows:
            return [(cm.to_object()) for (cm, _) in agg_rows]

        cat_models = (
            self.db.query(CategoryModel)
            .order_by(asc(CategoryModel.name))
            .limit(limit)
            .all()
        )
        return [cm.to_object() for cm in cat_models]

    def get_points_map(self, user_id: UUID) -> dict[UUID, int]:
        rows = (
            self.db.query(FeedPreference.category_id, FeedPreference.points)
            .filter_by(user_id=user_id)
            .all()
        )
        return {cid: int(points) for (cid, points) in rows}
