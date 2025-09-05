from dataclasses import dataclass
from uuid import UUID

from faker import Faker

from src.core.errors import DoesNotExistError, ExistsError
from src.core.users import User, UserRepository


@dataclass
class UserService:
    repo: UserRepository

    def register(self, mail: str, password: str) -> User:
        mail = mail.lower()
        if self.repo.read_by(mail=mail):
            raise ExistsError

        username = self.generate_unique_username()
        user = User(
            mail=mail,
            password=password,
            username=username,
            display_name=username,
        )
        return self.repo.create(user)

    def get_by_mail(self, mail: str) -> User:
        mail = mail.lower()
        user = self.repo.read_by(mail=mail)
        if not user:
            raise DoesNotExistError
        return user

    def get_by_username(self, username: str) -> User:
        user = self.repo.find_by_username(username)
        if not user:
            raise DoesNotExistError
        return user

    def update_user(
        self,
        user_id: UUID,
        *,
        username: str | None = None,
        display_name: str | None = None,
        bio: str | None = None,
        profile_pic: str | None = None,
    ) -> None:
        updates = {}
        if username:
            existing = self.repo.read_by(username=username)
            if existing and existing.id != user_id:
                raise ExistsError
            updates["username"] = username
        if display_name:
            updates["display_name"] = display_name
        if bio:
            updates["bio"] = bio
        if profile_pic:
            updates["profile_pic"] = profile_pic

        self.repo.update(user_id, updates)

    def generate_unique_username(self) -> str:
        faker = Faker()
        username = faker.unique.user_name()
        while self.repo.read_by(username=username):
            username = faker.unique.user_name()
        return str(username)
