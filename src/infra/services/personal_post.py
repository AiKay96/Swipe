from dataclasses import dataclass
from uuid import UUID

from src.core.errors import DoesNotExistError
from src.core.personal_post.comments import Comment, CommentRepository
from src.core.personal_post.likes import Like, LikeRepository
from src.core.personal_post.medias import Media, MediaRepository
from src.core.personal_post.posts import Post, PostRepository


@dataclass
class PersonalPostService:
    post_repo: PostRepository
    like_repo: LikeRepository
    comment_repo: CommentRepository
    media_repo: MediaRepository

    def create_post(self, user_id: UUID, description: str, media: list[Media]) -> Post:
        post = Post(user_id=user_id, description=description, media=media)
        self.media_repo.create_many(post.media)
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

    def comment_post(self, user_id: UUID, post_id: UUID, content: str) -> Comment:
        comment = Comment(user_id=user_id, post_id=post_id, content=content)
        return self.comment_repo.create(comment)

    def remove_comment(self, comment_id: UUID, user_id: UUID) -> None:
        comment = self.comment_repo.get(comment_id)
        if not comment or comment.user_id != user_id:
            raise DoesNotExistError
        self.comment_repo.delete(comment_id)
