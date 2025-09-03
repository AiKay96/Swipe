from dataclasses import dataclass
from uuid import UUID

from src.core.creator_post.likes import LikeRepository as CreatorPostLikeRepository
from src.core.creator_post.posts import Post as CreatorPost
from src.core.creator_post.saves import SaveRepository
from src.core.feed import FeedPost, Reaction
from src.core.personal_post.likes import LikeRepository as PersonalPostLikeRepository
from src.core.personal_post.posts import Post as PersonalPost


@dataclass
class PostDecorator:
    personal_post_like_repo: PersonalPostLikeRepository
    save_repo: SaveRepository
    creator_post_like_repo: CreatorPostLikeRepository

    def decorate_entity(
        self,
        user_id: UUID,
        post: PersonalPost | CreatorPost,
        *,
        is_creator: bool,
    ) -> FeedPost:
        if is_creator:
            like = self.creator_post_like_repo.get(user_id, post.id)
            if not like:
                reaction = Reaction.NONE
            else:
                reaction = Reaction.DISLIKE if like.is_dislike else Reaction.LIKE
            save = self.save_repo.get(user_id, post.id)
            is_saved = save is not None
            return FeedPost(post=post, reaction=reaction, is_saved=is_saved)

        like = self.creator_post_like_repo.get(user_id, post.id)
        if not like:
            reaction = Reaction.NONE
        else:
            reaction = Reaction.DISLIKE if like.is_dislike else Reaction.LIKE
        return FeedPost(post=post, reaction=reaction, is_saved=None)

    def decorate_list(
        self,
        user_id: UUID,
        posts: list[PersonalPost] | list[CreatorPost],
        *,
        is_creator: bool,
    ) -> list[FeedPost]:
        if not posts:
            return []

        ids = [p.id for p in posts]

        if is_creator:
            reactions = self.creator_post_like_repo.get_user_reactions(user_id, ids)
            saved_ids = set(self.save_repo.get_user_saves_for_posts(user_id, ids))
        else:
            reactions = self.personal_post_like_repo.get_user_reactions(user_id, ids)

        return [
            FeedPost(
                post=p,
                reaction=reactions.get(p.id, Reaction.NONE),
                is_saved=(p.id in saved_ids if is_creator else None),
            )
            for p in posts
        ]
