import math
from dataclasses import dataclass
from uuid import UUID

from src.core.errors import DoesNotExistError, ExistsError, ForbiddenError
from src.core.social import FriendStatus, SocialUser
from src.core.users import User, UserRepository
from src.infra.repositories.creator_post.categories import CategoryRepository
from src.infra.repositories.creator_post.feed_preferences import (
    FeedPreferenceRepository,
)
from src.infra.repositories.social import (
    FollowRepository,
    FriendRepository,
    SuggestionSkipRepository,
)


@dataclass
class SocialService:
    follow_repo: FollowRepository
    friend_repo: FriendRepository
    user_repo: UserRepository
    feed_pref_repo: FeedPreferenceRepository
    category_repo: CategoryRepository
    skip_repo: SuggestionSkipRepository

    def follow(self, user_id: UUID, target_id: UUID) -> None:
        if user_id == target_id:
            raise ForbiddenError("You cannot follow yourself.")

        if not self.user_repo.read_by(user_id=target_id):
            raise DoesNotExistError("Target user not found.")

        if self.follow_repo.get(user_id, target_id):
            raise ExistsError("Already following.")

        self.follow_repo.follow(user_id, target_id)

    def unfollow(self, user_id: UUID, target_id: UUID) -> None:
        if user_id == target_id:
            raise ForbiddenError("You cannot unfollow yourself.")

        if not self.user_repo.read_by(user_id=target_id):
            raise DoesNotExistError("Target user not found.")

        self.follow_repo.unfollow(user_id, target_id)

    def send_friend_request(self, from_user_id: UUID, to_user_id: UUID) -> None:
        if from_user_id == to_user_id:
            raise ForbiddenError("You cannot send a friend request to yourself.")

        if not self.user_repo.read_by(user_id=to_user_id):
            raise DoesNotExistError("Target user not found.")

        existing = self.friend_repo.get_friend(from_user_id, to_user_id)
        if existing:
            raise ExistsError("You are already friends.")

        request = self.friend_repo.get_request(from_user_id, to_user_id)
        if request:
            raise ExistsError("Friend request already sent.")

        self.friend_repo.send_request(from_user_id, to_user_id)

    def cancel_friend_request(self, from_user_id: UUID, to_user_id: UUID) -> None:
        self.friend_repo.delete_request(from_user_id, to_user_id)

    def accept_friend_request(self, from_user_id: UUID, to_user_id: UUID) -> None:
        if from_user_id == to_user_id:
            raise ForbiddenError("Invalid friend request.")

        if not self.user_repo.read_by(user_id=from_user_id):
            raise DoesNotExistError("User not exist anymore.")

        if self.friend_repo.get_friend(from_user_id, to_user_id):
            raise ExistsError("Already friends.")

        request = self.friend_repo.get_request(from_user_id, to_user_id)
        if not request:
            raise DoesNotExistError("No friend request to accept.")

        self.friend_repo.accept_request(from_user_id, to_user_id)

    def decline_friend_request(self, from_user_id: UUID, to_user_id: UUID) -> None:
        self.friend_repo.delete_request(from_user_id, to_user_id)

    def skip_suggestion(
        self, user_id: UUID, target_id: UUID, ttl_days: int | None = None
    ) -> None:
        if (
            self.is_following(user_id, target_id)
            or target_id in self.friend_repo.get_friend_ids(user_id)
            or target_id in self.friend_repo.get_requests_from(user_id)
            or target_id in self.friend_repo.get_requests_to(user_id)
        ):
            return
        self.skip_repo.skip(user_id, target_id, ttl_days=ttl_days)

    def get_followers(self, user_id: UUID) -> list[User]:
        ids = self.follow_repo.get_followers(user_id)
        return self.user_repo.read_many_by_ids(ids)

    def get_following(self, user_id: UUID) -> list[User]:
        ids = self.follow_repo.get_following(user_id)
        return self.user_repo.read_many_by_ids(ids)

    def get_incoming_friend_requests(self, user_id: UUID) -> list[User]:
        ids = self.friend_repo.get_requests_to(user_id)
        return self.user_repo.read_many_by_ids(ids)

    def get_friends(self, user_id: UUID) -> list[User]:
        ids = self.friend_repo.get_friend_ids(user_id)
        return self.user_repo.read_many_by_ids(ids)

    def get_friend_status(self, user_id: UUID, other_id: UUID) -> FriendStatus:
        if not self.user_repo.read_by(user_id=other_id):
            raise DoesNotExistError("User not exist anymore.")
        if self.friend_repo.get_friend(user_id, other_id):
            return FriendStatus.FRIENDS
        if self.friend_repo.get_request(user_id, other_id):
            return FriendStatus.PENDING_OUTGOING
        if self.friend_repo.get_request(other_id, user_id):
            return FriendStatus.PENDING_INCOMING
        return FriendStatus.NOT_FRIENDS

    def is_following(self, user_id: UUID, other_id: UUID) -> bool:
        if not self.user_repo.read_by(user_id=other_id):
            raise DoesNotExistError("User not exist anymore.")
        return self.follow_repo.get(user_id, other_id) is not None

    def _cosine_0_1(self, a: dict[UUID, int], b: dict[UUID, int]) -> float:
        if not a and not b:
            return 0.0

        keys = set(a.keys()) | set(b.keys())
        dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))

        if na == 0.0 or nb == 0.0:
            return 0.0

        cos = dot / (na * nb)
        return max(0.0, min(1.0, 0.5 * (cos + 1.0)))

    def calculate_match_rate(self, user_id: UUID, other_id: UUID) -> int:
        if user_id == other_id:
            return 100

        interest_sim = self._cosine_0_1(
            self.feed_pref_repo.get_points_map(user_id),
            self.feed_pref_repo.get_points_map(other_id),
        )

        my_friends = set(self.friend_repo.get_friend_ids(user_id))
        their_friends = set(self.friend_repo.get_friend_ids(other_id))
        mutuals = len(my_friends & their_friends)

        mutual_bonus = min(0.05 * mutuals, 0.25)

        raw_score = min(1.0, interest_sim + mutual_bonus)
        return int(round(raw_score * 100))

    def overlap_categories(self, user_id: UUID, other_id: UUID) -> list[str]:
        category_names = self.category_repo.get_all_names()

        a_full = self.feed_pref_repo.get_points_map(user_id)
        b_full = self.feed_pref_repo.get_points_map(other_id)
        a = {cid: v for cid, v in a_full.items() if v > 0}
        b = {cid: v for cid, v in b_full.items() if v > 0}

        common = set(a.keys()) & set(b.keys())
        if not common:
            return []

        scored: list[tuple[UUID, int, int]] = []
        for cid in common:
            av, bv = a[cid], b[cid]
            strength = min(av, bv)
            balance = -abs(av - bv)
            scored.append((cid, strength, balance))

        scored.sort(key=lambda t: (t[1], t[2]), reverse=True)
        top_ids = [cid for cid, _, _ in scored[:3]]

        return [category_names.get(cid, str(cid)[:8]) for cid in top_ids]

    def get_friend_suggestions(
        self, user_id: UUID, limit: int = 20
    ) -> list[SocialUser]:
        my_friends = set(self.friend_repo.get_friend_ids(user_id))

        fof: set[UUID] = set()
        for f in my_friends:
            fof.update(self.friend_repo.get_friend_ids(f))

        fof.discard(user_id)
        fof -= my_friends
        fof -= set(self.friend_repo.get_requests_to(user_id))
        fof -= set(self.friend_repo.get_requests_from(user_id))

        fof -= self.skip_repo.get_skipped_ids(user_id)

        if not fof:
            return []

        results: list[SocialUser] = []

        for suggestion_id in fof:
            suggestion = self.user_repo.read_by(user_id=suggestion_id)
            if not suggestion:
                continue
            social_user = SocialUser(
                user=suggestion,
                friend_status=self.get_friend_status(user_id, suggestion_id),
                is_following=self.is_following(user_id, suggestion_id),
                mutual_friend_count=len(
                    my_friends & set(self.friend_repo.get_friend_ids(suggestion_id))
                ),
                match_rate=self.calculate_match_rate(user_id, suggestion_id),
                overlap_categories=self.overlap_categories(user_id, suggestion_id),
            )
            results.append(social_user)

        results.sort(
            key=lambda user: (user.match_rate, user.mutual_friend_count), reverse=True
        )
        return results[:limit]
