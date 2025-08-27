from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from src.infra.models.follow import Follow
from src.infra.models.friend import Friend, FriendRequest


@dataclass
class FollowRepository:
    db: Session

    def get(self, follower_id: UUID, following_id: UUID) -> Follow | None:
        return (
            self.db.query(Follow)
            .filter_by(follower_id=follower_id, following_id=following_id)
            .first()
        )

    def follow(self, follower_id: UUID, following_id: UUID) -> None:
        self.db.add(Follow(follower_id=follower_id, following_id=following_id))
        self.db.commit()

    def unfollow(self, follower_id: UUID, following_id: UUID) -> None:
        self.db.query(Follow).filter_by(
            follower_id=follower_id, following_id=following_id
        ).delete()
        self.db.commit()

    def get_followers(self, user_id: UUID) -> list[UUID]:
        return [
            follow.follower_id
            for follow in self.db.query(Follow).filter_by(following_id=user_id).all()
        ]

    def get_following(self, user_id: UUID) -> list[UUID]:
        return [
            follow.following_id
            for follow in self.db.query(Follow).filter_by(follower_id=user_id).all()
        ]


@dataclass
class FriendRepository:
    db: Session

    def get_request(self, from_user_id: UUID, to_user_id: UUID) -> FriendRequest | None:
        return (
            self.db.query(FriendRequest)
            .filter_by(from_user_id=from_user_id, to_user_id=to_user_id)
            .first()
        )

    def get_friend(self, user_id: UUID, friend_id: UUID) -> Friend | None:
        return (
            self.db.query(Friend)
            .filter_by(user_id=user_id, friend_id=friend_id)
            .first()
        )

    def send_request(self, from_user_id: UUID, to_user_id: UUID) -> None:
        self.db.add(FriendRequest(from_user_id=from_user_id, to_user_id=to_user_id))
        self.db.commit()

    def delete_request(self, from_user_id: UUID, to_user_id: UUID) -> None:
        self.db.query(FriendRequest).filter_by(
            from_user_id=from_user_id, to_user_id=to_user_id
        ).delete()
        self.db.commit()

    def accept_request(self, from_user_id: UUID, to_user_id: UUID) -> None:
        req = (
            self.db.query(FriendRequest)
            .filter_by(from_user_id=from_user_id, to_user_id=to_user_id)
            .first()
        )
        if not req:
            return

        self.db.delete(req)

        self.db.add(Friend(user_id=from_user_id, friend_id=to_user_id))
        self.db.add(Friend(user_id=to_user_id, friend_id=from_user_id))

        self.db.commit()

    def get_requests_to(self, user_id: UUID) -> list[UUID]:
        return [
            req.from_user_id
            for req in self.db.query(FriendRequest).filter_by(to_user_id=user_id).all()
        ]

    def get_requests_from(self, user_id: UUID) -> list[UUID]:
        return [
            req.from_user_id
            for req in self.db.query(FriendRequest)
            .filter_by(from_user_id=user_id)
            .all()
        ]

    def get_friend_ids(self, user_id: UUID) -> list[UUID]:
        return [
            friend.friend_id
            for friend in self.db.query(Friend).filter_by(user_id=user_id).all()
        ]
