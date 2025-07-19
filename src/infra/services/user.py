from dataclasses import dataclass

from faker import Faker

from src.core.users import User, UserRepository

faker = Faker()


@dataclass
class UserService:
    repo: UserRepository

    def register(self, user: User) -> None:
        self.repo.create(user)

    def get_by_mail(self, mail: str) -> User | None:
        return self.repo.read_by_mail(mail)
