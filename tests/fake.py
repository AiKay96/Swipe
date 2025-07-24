from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from faker import Faker

from src.core.personal_post.comments import Comment as PersonalPostComment
from src.core.personal_post.likes import Like as PersonalPostLike
from src.core.personal_post.medias import Media, MediaType
from src.core.personal_post.posts import Post as PersonalPost
from src.core.users import User

_faker = Faker()


@dataclass(frozen=True)
class FakeUser:
    mail: str = field(default_factory=lambda: _faker.email())
    password: str = field(default_factory=lambda: _faker.password())
    username: str = field(default_factory=lambda: _faker.unique.user_name())
    display_name: str = field(default_factory=lambda: _faker.unique.name())
    bio: str = field(default_factory=lambda: _faker.sentence(nb_words=3))
    id: UUID = field(default_factory=lambda: UUID(_faker.uuid4()))

    def as_dict(self) -> dict[str, Any]:
        return {
            "mail": self.mail,
            "password": self.password,
            "username": self.username,
            "display_name": self.display_name,
            "bio": self.bio,
        }

    def as_create_dict(self) -> dict[str, str]:
        return {
            "mail": self.mail,
            "password": self.password,
        }

    def as_user(self) -> User:
        return User(
            mail=self.mail,
            password=self.password,
            username=self.username,
            display_name=self.display_name,
            bio=self.bio,
        )


@dataclass(frozen=True)
class FakePersonalPost:
    user_id: UUID = field(default_factory=uuid4)
    description: str = field(default_factory=lambda: _faker.sentence(nb_words=6))
    like_count: int = 0
    dislike_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: UUID = field(default_factory=uuid4)

    def as_post(self) -> PersonalPost:
        return PersonalPost(
            id=self.id,
            user_id=self.user_id,
            description=self.description,
            like_count=self.like_count,
            dislike_count=self.dislike_count,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class FakePersonalPostComment:
    post_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    content: str = field(default_factory=lambda: _faker.sentence(nb_words=8))
    id: UUID = field(default_factory=uuid4)

    def as_comment(self) -> PersonalPostComment:
        return PersonalPostComment(
            id=self.id,
            post_id=self.post_id,
            user_id=self.user_id,
            content=self.content,
        )


@dataclass(frozen=True)
class FakePersonalPostLike:
    post_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    is_dislike: bool = False
    id: UUID = field(default_factory=uuid4)

    def as_like(self) -> PersonalPostLike:
        return PersonalPostLike(
            id=self.id,
            post_id=self.post_id,
            user_id=self.user_id,
            is_dislike=self.is_dislike,
        )


@dataclass(frozen=True)
class FakePersonalPostMedia:
    post_id: UUID = field(default_factory=uuid4)
    url: str = field(default_factory=lambda: _faker.image_url())
    media_type: str = MediaType.IMAGE.value
    id: UUID = field(default_factory=uuid4)

    def as_media(self) -> Media:
        return Media(
            id=self.id,
            post_id=self.post_id,
            url=self.url,
            media_type=MediaType(self.media_type),
        )
