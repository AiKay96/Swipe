from dataclasses import dataclass
from enum import Enum

from src.core.personal_post.posts import Post


class Reaction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    NONE = "none"


@dataclass
class FeedPost:
    post: Post
    reaction: Reaction = Reaction.NONE
