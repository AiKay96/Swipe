from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.creator_post.posts import Post
from src.core.errors import DoesNotExistError, ForbiddenError
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


@dataclass
class PostRepository:
    db: Session

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
        self.db.refresh(db_post)
        return db_post.to_object()

    def get(self, post_id: UUID) -> Post | None:
        db_post = self.db.query(PostModel).filter_by(id=post_id).first()
        return db_post.to_object() if db_post else None

    def get_posts_by_user(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
    ) -> list[Post]:
        posts = (
            self.db.query(PostModel)
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

        query = self.db.query(PostModel).filter(
            PostModel.user_id.in_(user_ids),
            PostModel.created_at < before,
        )

        if category_filter is not None:
            query = query.filter(PostModel.category_id == category_filter)

        posts = query.order_by(PostModel.created_at.desc()).limit(limit).all()

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
