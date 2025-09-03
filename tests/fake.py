from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from faker import Faker

from src.core.creator_post.categories import Category
from src.core.creator_post.posts import Post as CreatorPost
from src.core.creator_post.references import Reference
from src.core.creator_post.saves import Save
from src.core.personal_post.comments import Comment as PersonalPostComment
from src.core.personal_post.likes import Like as PersonalPostLike
from src.core.personal_post.posts import Media, MediaType, Privacy
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
    created_at: datetime = field(default_factory=datetime.now)
    privacy: Privacy = Privacy.FRIENDS_ONLY
    media: list[Media] = field(
        default_factory=lambda: [
            Media(url=_faker.image_url(), media_type=MediaType.IMAGE)
        ]
    )

    comments: list[PersonalPostComment] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def as_post(self) -> PersonalPost:
        return PersonalPost(
            id=self.id,
            user_id=self.user_id,
            description=self.description,
            like_count=self.like_count,
            dislike_count=self.dislike_count,
            created_at=self.created_at,
            privacy=self.privacy,
            media=self.media,
            comments=self.comments,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "media": [
                {"url": m.url, "media_type": m.media_type.value} for m in self.media
            ],
        }


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
class FakeCategory:
    name: str = "Movies"
    tag_names: list[str] = field(default_factory=lambda: ["Drama", "Sci-fi"])
    id: UUID = field(default_factory=uuid4)

    def as_category(self) -> Category:
        return Category(
            id=self.id,
            name=self.name,
            tag_names=self.tag_names,
        )


@dataclass(frozen=True)
class FakeReference:
    title: str = "The Shawshank Redemption"
    description: str = (
        "Two imprisoned men bond over a number of years, finding "
        + "solace and eventual redemption through acts of common decency."
    )
    image_url: str = (
        "https://image.tmdb.org/t/p/original/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg"
    )
    tag_names: list[str] = field(default_factory=lambda: ["Drama"])
    attributes: dict[str, Any] = field(
        default_factory=lambda: {
            "release_year": 1994,
            "duration_minutes": 142,
            "director": "Frank Darabont",
        }
    )

    def as_reference(self) -> Reference:
        return Reference(
            title=self.title,
            description=self.description,
            image_url=self.image_url,
            tag_names=self.tag_names,
            attributes=self.attributes,
        )


@dataclass(frozen=True)
class FakeCreatorPost:
    user_id: UUID = field(default_factory=uuid4)
    description: str = field(default_factory=lambda: _faker.sentence(nb_words=6))
    like_count: int = 0
    dislike_count: int = 0
    category_id: UUID | None = None
    reference_id: UUID | None = None
    created_at: datetime = field(default_factory=datetime.now)
    category_tag_names: list[str] = field(default_factory=list)
    hashtag_names: list[str] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def as_post(self) -> CreatorPost:
        return CreatorPost(
            id=self.id,
            user_id=self.user_id,
            category_id=self.category_id,
            reference_id=self.reference_id,
            description=self.description,
            like_count=self.like_count,
            dislike_count=self.dislike_count,
            created_at=self.created_at,
            category_tag_names=self.category_tag_names,
            hashtag_names=self.hashtag_names,
        )

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "description": self.description,
            "media": [
                {
                    "url": "https://example.com/test.jpg",
                    "media_type": MediaType.IMAGE.value,
                }
            ],
            "category_tag_names": list(self.category_tag_names),
            "hashtag_names": list(self.hashtag_names),
        }
        payload["category_id"] = (
            str(self.category_id) if self.category_id else _faker.uuid4()
        )
        payload["reference_id"] = (
            str(self.reference_id) if self.reference_id else _faker.uuid4()
        )
        return payload


@dataclass(frozen=True)
class FakeSave:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    post_id: UUID = field(default_factory=uuid4)

    def as_save(self) -> Save:
        return Save(
            user_id=self.user_id,
            post_id=self.post_id,
        )
