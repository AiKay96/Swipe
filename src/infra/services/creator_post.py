from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.core.creator_post.comments import Comment, CommentRepository
from src.core.creator_post.likes import Like, LikeRepository
from src.core.creator_post.posts import Media, Post, PostRepository
from src.core.creator_post.saves import Save, SaveRepository
from src.core.errors import DoesNotExistError
from src.infra.repositories.creator_post.feed_preferences import (
    FeedPreferenceRepository,
)


@dataclass
class CreatorPostService:
    post_repo: PostRepository
    like_repo: LikeRepository
    comment_repo: CommentRepository
    save_repo: SaveRepository
    feed_pref_repo: FeedPreferenceRepository

    def create_post(
        self,
        user_id: UUID,
        category_id: UUID,
        reference_id: UUID,
        description: str,
        category_tag_names: list[str],
        hashtag_names: list[str],
        media: list[Media],
    ) -> Post:
        post = Post(
            user_id=user_id,
            category_id=category_id,
            reference_id=reference_id,
            description=description,
            category_tag_names=category_tag_names,
            hashtag_names=hashtag_names,
            media=media,
        )
        return self.post_repo.create(post)

    def delete_post(self, post_id: UUID, user_id: UUID) -> None:
        post = self.post_repo.get(post_id)
        if not post or post.user_id != user_id:
            raise DoesNotExistError
        self.post_repo.delete(post_id)

    def like_post(self, user_id: UUID, post_id: UUID) -> None:
        post = self.post_repo.get(post_id)
        if not post:
            raise DoesNotExistError

        existing = self.like_repo.get(user_id, post_id)
        if existing:
            if existing.is_dislike:
                self.like_repo.update(existing.id, is_dislike=False)
                self.post_repo.update_like_counts(
                    post_id=post_id, like_count_delta=1, dislike_count_delta=-1
                )
        else:
            self.like_repo.create(Like(user_id=user_id, post_id=post_id))
            self.post_repo.update_like_counts(post_id=post_id, like_count_delta=1)
        self._record_interaction(user_id, post, "like")

    def dislike_post(self, user_id: UUID, post_id: UUID) -> None:
        post = self.post_repo.get(post_id)
        if not post:
            raise DoesNotExistError

        existing = self.like_repo.get(user_id, post_id)
        if existing:
            if not existing.is_dislike:
                self.like_repo.update(existing.id, is_dislike=True)
                self.post_repo.update_like_counts(
                    post_id=post_id, like_count_delta=-1, dislike_count_delta=1
                )
        else:
            self.like_repo.create(
                Like(user_id=user_id, post_id=post_id, is_dislike=True)
            )
            self.post_repo.update_like_counts(post_id=post_id, dislike_count_delta=1)
        self._record_interaction(user_id, post, "dislike")

    def unlike_post(self, user_id: UUID, post_id: UUID) -> None:
        post = self.post_repo.get(post_id)
        if not post:
            raise DoesNotExistError

        existing = self.like_repo.get(user_id, post_id)
        if not existing:
            return

        if existing.is_dislike:
            self.post_repo.update_like_counts(post_id=post_id, dislike_count_delta=-1)
        else:
            self.post_repo.update_like_counts(post_id=post_id, like_count_delta=-1)

        self.like_repo.delete(existing.id)
        self._record_interaction(user_id, post, "unlike")

    def save_post(self, user_id: UUID, post_id: UUID) -> None:
        post = self.post_repo.get(post_id)
        if not post:
            raise DoesNotExistError

        existing = self.save_repo.get(user_id, post_id)
        if not existing:
            self.save_repo.create(Save(post_id, user_id))
        self._record_interaction(user_id, post, "save")

    def remove_save(self, user_id: UUID, post_id: UUID) -> None:
        post = self.post_repo.get(post_id)
        if not post:
            raise DoesNotExistError

        existing = self.save_repo.get(user_id, post_id)
        if existing:
            self.save_repo.delete(existing.id)
            self._record_interaction(user_id, post, "unsave")

    def comment_post(self, user_id: UUID, post_id: UUID, content: str) -> None:
        post = self.post_repo.get(post_id)
        if not post:
            raise DoesNotExistError
        comment = Comment(user_id=user_id, post_id=post_id, content=content)
        self.comment_repo.create(comment)
        self._record_interaction(user_id, post, "comment")

    def remove_comment(self, post_id: UUID, comment_id: UUID, user_id: UUID) -> None:
        post = self.post_repo.get(post_id)
        if not post:
            raise DoesNotExistError
        comment = self.comment_repo.get(comment_id)
        if not comment or comment.user_id != user_id or comment.post_id != post_id:
            raise DoesNotExistError
        self.comment_repo.delete(comment_id)
        self._record_interaction(user_id, post, "uncomment")

    def get_user_posts(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
    ) -> list[Post]:
        return self.post_repo.get_posts_by_user(
            user_id=user_id,
            limit=limit,
            before=before,
        )

    def get_user_saves(
        self,
        user_id: UUID,
        limit: int,
        before: datetime,
    ) -> list[Post]:
        return self.post_repo.get_saved_posts_by_user(
            user_id=user_id,
            limit=limit,
            before=before,
        )

    def _record_interaction(self, user_id: UUID, post: Post, action: str) -> None:
        if not post.category_id:
            return
        weights = {
            "save": 5,
            "comment": 3,
            "like": 2,
            "dislike": -2,
            "unsave": -4,
            "uncomment": -2,
            "unlike": -1,
        }
        delta = weights.get(action)
        if delta:
            self.feed_pref_repo.add_points(user_id, post.category_id, delta)
