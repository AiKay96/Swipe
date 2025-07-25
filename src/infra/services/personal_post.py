from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.core.errors import DoesNotExistError
from src.core.personal_post.comments import Comment, CommentRepository
from src.core.personal_post.likes import Like, LikeRepository
from src.core.personal_post.posts import Media, Post, PostRepository, Privacy


@dataclass
class PersonalPostService:
    post_repo: PostRepository
    like_repo: LikeRepository
    comment_repo: CommentRepository

    def create_post(self, user_id: UUID, description: str, media: list[Media]) -> Post:
        post = Post(user_id=user_id, description=description, media=media)
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

    def change_privacy(self, user_id: UUID, post_id: UUID) -> None:
        post = self.post_repo.get(post_id)
        if not post or post.user_id != user_id:
            raise DoesNotExistError

        if post.privacy == Privacy.FRIENDS_ONLY:
            self.post_repo.update_privacy(post_id, Privacy.PUBLIC)
        else:
            self.post_repo.update_privacy(post_id, Privacy.FRIENDS_ONLY)

    def comment_post(self, user_id: UUID, post_id: UUID, content: str) -> None:
        comment = Comment(user_id=user_id, post_id=post_id, content=content)
        self.comment_repo.create(comment)

    def remove_comment(self, post_id: UUID, comment_id: UUID, user_id: UUID) -> None:
        comment = self.comment_repo.get(comment_id)
        if not comment or comment.user_id != user_id or comment.post_id != post_id:
            raise DoesNotExistError
        self.comment_repo.delete(comment_id)

    def get_user_posts(
        self,
        user_id: UUID,
        limit: int,
        before: datetime | None,
        include_friends_only: bool = False,
    ) -> list[Post]:
        return self.post_repo.get_posts_by_user(
            user_id=user_id,
            limit=limit,
            before=before,
            include_friends_only=include_friends_only,
        )
