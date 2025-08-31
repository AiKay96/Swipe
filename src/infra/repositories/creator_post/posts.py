from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session, selectinload

from src.core.creator_post.posts import Post
from src.core.errors import DoesNotExistError, ForbiddenError
from src.infra.models.creator_post.category import Category
from src.infra.models.creator_post.category_tag import CategoryTag
from src.infra.models.creator_post.hashtag import (
    Hashtag as HashtagModel,
)
from src.infra.models.creator_post.hashtag import (
    creator_post_hashtags,
)
from src.infra.models.creator_post.media import Media as MediaModel
from src.infra.models.creator_post.post import Post as PostModel
from src.infra.models.creator_post.reference import Reference
from src.infra.models.creator_post.reference import Reference as ReferenceModel
from src.infra.models.user import User


@dataclass
class PostRepository:
    db: Session

    def _with_eager(self, query: Query[PostModel]) -> Query[PostModel]:
        return query.options(
            selectinload(PostModel.user).load_only(User.id, User.username),
            selectinload(PostModel.category).load_only(Category.id, Category.name),
            selectinload(PostModel.reference).load_only(
                ReferenceModel.id, ReferenceModel.title
            ),
            selectinload(PostModel.media),
            selectinload(PostModel.comments),
        )

    def create(self, post: Post) -> Post:
        if post.category_id:
            category_exists = (
                self.db.query(CategoryTag.category_id)
                .filter_by(category_id=post.category_id)
                .first()
            )
            if not category_exists:
                raise DoesNotExistError("Category does not exist.")

        if post.category_tag_names and post.category_id:
            tags = (
                self.db.query(CategoryTag)
                .filter(
                    CategoryTag.category_id == post.category_id,
                    CategoryTag.name.in_(post.category_tag_names),
                )
                .all()
            )
            found_names = {t.name for t in tags}
            missing = set(post.category_tag_names) - found_names
            if missing:
                raise ForbiddenError(f"CategoryTag(s) not found in category: {missing}")

        if post.reference_id:
            exists = self.db.query(Reference).filter_by(id=post.reference_id).first()
            if not exists:
                raise DoesNotExistError("Reference does not exist.")

        hashtags = []
        for name in post.hashtag_names:
            hashtag = self.db.query(HashtagModel).filter_by(name=name).first()
            if not hashtag:
                hashtag = HashtagModel(name=name)
                self.db.add(hashtag)
                self.db.flush()
            hashtags.append(hashtag)

        db_post = PostModel(
            user_id=post.user_id,
            category_id=post.category_id,
            reference_id=post.reference_id,
            description=post.description,
            like_count=post.like_count,
            dislike_count=post.dislike_count,
            category_tag_names=post.category_tag_names,
            hashtag_names=post.hashtag_names,
        )
        self.db.add(db_post)
        self.db.flush()

        db_post.hashtags = hashtags
        db_post.media = [
            MediaModel(post_id=db_post.id, url=m.url, media_type=m.media_type.value)
            for m in post.media
        ]

        self.db.commit()
        refetched = (
            self._with_eager(self.db.query(PostModel)).filter_by(id=db_post.id).first()
        )
        if refetched is None:
            raise DoesNotExistError("Post not found after create.")
        return refetched.to_object()

    def get(self, post_id: UUID) -> Post | None:
        db_post = (
            self._with_eager(self.db.query(PostModel)).filter_by(id=post_id).first()
        )
        return db_post.to_object() if db_post else None

    def batch_get(self, ids: list[UUID]) -> list[Post]:
        if not ids:
            return []

        rows = (
            self._with_eager(self.db.query(PostModel))
            .filter(PostModel.id.in_(ids))
            .all()
        )
        by_id = {r.id: r.to_object() for r in rows}
        return [by_id[i] for i in ids if i in by_id]

    def get_posts_by_user(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
    ) -> list[Post]:
        posts = (
            self._with_eager(self.db.query(PostModel))
            .filter(
                PostModel.user_id == user_id,
                PostModel.created_at < before,
            )
            .order_by(PostModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [p.to_object() for p in posts]

    def get_posts_by_users(
        self,
        user_ids: list[UUID],
        before: datetime,
        limit: int,
        category_filter: UUID | None = None,
    ) -> list[Post]:
        if not user_ids:
            return []

        query = self._with_eager(self.db.query(PostModel)).filter(
            PostModel.user_id.in_(user_ids),
            PostModel.created_at < before,
        )

        if category_filter is not None:
            query = query.filter(PostModel.category_id == category_filter)

        posts = query.order_by(PostModel.created_at.desc()).limit(limit).all()
        return [p.to_object() for p in posts]

    def get_saved_posts_by_user(
        self, user_id: UUID, limit: int, before: datetime
    ) -> list[Post]:
        posts = (
            self._with_eager(self.db.query(PostModel))
            .join(PostModel._saves)
            .filter(
                PostModel._saves.any(user_id=user_id),
                PostModel.created_at < before,
            )
            .order_by(PostModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [p.to_object() for p in posts]

    def update_like_counts(
        self, post_id: UUID, like_count_delta: int = 0, dislike_count_delta: int = 0
    ) -> None:
        post = self.db.query(PostModel).filter_by(id=post_id).first()
        if not post:
            raise DoesNotExistError("Post not found.")

        post.like_count += like_count_delta
        post.dislike_count += dislike_count_delta
        self.db.commit()

    def delete(self, post_id: UUID) -> None:
        post = self.db.query(PostModel).filter_by(id=post_id).first()
        if not post:
            raise DoesNotExistError("Post not found.")

        hashtags = list(post.hashtags)
        self.db.delete(post)
        self.db.commit()

        for hashtag in hashtags:
            remaining = (
                self.db.query(creator_post_hashtags)
                .filter_by(tag_id=hashtag.id)
                .first()
            )
            if not remaining:
                self.db.delete(hashtag)

        self.db.commit()

    def get_posts_by_users_in_category(
        self,
        user_ids: list[UUID],
        category_id: UUID,
        exclude_ids: list[UUID],
        limit: int,
        before: datetime,
    ) -> list[Post]:
        if not user_ids:
            return []

        query = self._with_eager(self.db.query(PostModel)).filter(
            PostModel.user_id.in_(user_ids),
            PostModel.category_id == category_id,
            PostModel.created_at < before,
        )

        if exclude_ids:
            query = query.filter(~PostModel.id.in_(exclude_ids))

        posts = query.order_by(PostModel.created_at.desc()).limit(limit).all()
        return [p.to_object() for p in posts]

    def get_trending_posts_in_category(
        self,
        category_id: UUID,
        exclude_user_ids: list[UUID],
        exclude_post_ids: list[UUID],
        limit: int,
        days: int = 30,
    ) -> list[Post]:
        cutoff = datetime.now() - timedelta(days=days)

        posts = (
            self._with_eager(self.db.query(PostModel))
            .filter(
                PostModel.category_id == category_id,
                PostModel.created_at > cutoff,
                ~PostModel.user_id.in_(exclude_user_ids),
                ~PostModel.id.in_(exclude_post_ids),
            )
            .order_by(
                (PostModel.like_count + PostModel.dislike_count).desc(),
                PostModel.created_at.desc(),
            )
            .limit(limit)
            .all()
        )
        return [p.to_object() for p in posts]

    def search(
        self,
        query: str,
        *,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Post]:
        ts_query = func.plainto_tsquery("english", query)

        ts_vector = (
            func.to_tsvector("english", PostModel.description)
            + func.to_tsvector(
                "english", func.array_to_string(PostModel.category_tag_names, " ")
            )
            + func.to_tsvector(
                "english", func.array_to_string(PostModel.hashtag_names, " ")
            )
            + func.to_tsvector("english", func.coalesce(ReferenceModel.title, ""))
        )

        q = (
            self._with_eager(self.db.query(PostModel))
            .outerjoin(ReferenceModel, PostModel.reference_id == ReferenceModel.id)
            .filter(
                or_(
                    ts_vector.op("@@")(ts_query),
                    PostModel.description.ilike(f"%{query}%"),
                    func.similarity(PostModel.description, query) > 0.3,
                )
            )
        )

        if before is not None:
            q = q.filter(PostModel.created_at < before)

        posts = (
            q.order_by(func.similarity(PostModel.description, query).desc())
            .limit(limit)
            .all()
        )
        return [p.to_object() for p in posts]
