from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from uuid import UUID

from .users import User


class FriendStatus(str, Enum):
    NOT_FRIENDS = "not_friends"
    PENDING_OUTGOING = "pending_outgoing"
    PENDING_INCOMING = "pending_incoming"
    FRIENDS = "friends"


@dataclass
class SocialUser:
    user: User
    friend_status: FriendStatus
    is_following: bool
    mutual_friend_count: int
    match_rate: int
    overlap_categories: list[str]


class SocialService(Protocol):
    def follow(self, user_id: UUID, target_id: UUID) -> None: ...

    def unfollow(self, user_id: UUID, target_id: UUID) -> None: ...

    def send_friend_request(self, from_user_id: UUID, to_user_id: UUID) -> None: ...

    def cancel_friend_request(self, from_user_id: UUID, to_user_id: UUID) -> None: ...

    def accept_friend_request(self, from_user_id: UUID, to_user_id: UUID) -> None: ...

    def decline_friend_request(self, from_user_id: UUID, to_user_id: UUID) -> None: ...

    def skip_suggestion(
        self, user_id: UUID, target_id: UUID, ttl_days: int | None = None
    ) -> None: ...

    def get_followers(self, user_id: UUID) -> list[User]: ...

    def get_following(self, user_id: UUID) -> list[User]: ...

    def get_incoming_friend_requests(self, user_id: UUID) -> list[User]: ...

    def get_friends(self, user_id: UUID) -> list[User]: ...

    def get_friend_status(self, user_id: UUID, other_id: UUID) -> FriendStatus: ...

    def is_following(self, user_id: UUID, other_id: UUID) -> bool: ...

    def calculate_match_rate(self, user_id: UUID, other_id: UUID) -> int: ...

    def overlap_categories(self, user_id: UUID, other_id: UUID) -> list[str]: ...

    def get_friend_suggestions(self, user_id: UUID, limit: int) -> list[SocialUser]: ...
