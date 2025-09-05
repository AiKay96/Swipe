from dataclasses import dataclass
from uuid import UUID

from src.core.social import SocialService, SocialUser
from src.core.users import User


@dataclass
class UserDecorator:
    social: SocialService

    def decorate_entity(
        self,
        user_id: UUID,
        user: User,
    ) -> SocialUser:
        # Fetch once; avoid re-calling service
        user_friends = self.social.get_friends(user_id)  # list[User] (assumed)
        other_friends = self.social.get_friends(user.id)  # list[User] (assumed)

        # Use IDs to build sets (hashable)
        user_friend_ids = {u.id for u in user_friends}
        other_friend_ids = {u.id for u in other_friends}

        return SocialUser(
            user=user,
            friend_status=self.social.get_friend_status(user_id, user.id),
            is_following=self.social.is_following(user_id, user.id),
            mutual_friend_count=len(user_friend_ids & other_friend_ids),
            match_rate=self.social.calculate_match_rate(user_id, user.id),
            overlap_categories=self.social.overlap_categories(user_id, user.id),
        )
