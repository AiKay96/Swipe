from dataclasses import dataclass
from uuid import UUID

from src.core.errors import DoesNotExistError, ExistsError, ForbiddenError
from src.core.social import FriendStatus
from src.core.users import User, UserRepository
from src.infra.repositories.social import FollowRepository, FriendRepository


@dataclass
class SocialService:
    follow_repo: FollowRepository
    friend_repo: FriendRepository
    user_repo: UserRepository

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

    def get_friend_suggestions(self, user_id: UUID, limit: int = 20) -> list[User]:
        my_friends = set(self.friend_repo.get_friend_ids(user_id))

        fof: set[UUID] = set()
        for f in my_friends:
            fof.update(self.friend_repo.get_friend_ids(f))

        fof.discard(user_id)
        fof -= my_friends
        fof -= set(self.friend_repo.get_requests_to(user_id))
        fof -= set(self.friend_repo.get_requests_from(user_id))

        scored: list[tuple[int, UUID]] = []
        for cid in fof:
            their_friends = set(self.friend_repo.get_friend_ids(cid))
            mutuals = len(my_friends & their_friends)
            scored.append((mutuals, cid))

        scored.sort(key=lambda t: t[0], reverse=True)
        chosen_ids = [cid for _, cid in scored[:limit]]

        users_by_id = {u.id: u for u in self.user_repo.read_many_by_ids(chosen_ids)}
        return [users_by_id[cid] for cid in chosen_ids if cid in users_by_id]
