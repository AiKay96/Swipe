from dataclasses import dataclass

from faker import Faker

from src.core.errors import DoesNotExistError, ExistsError
from src.core.users import User, UserRepository


@dataclass
class UserService:
    repo: UserRepository

    def register(self, mail: str, password: str) -> User:
        if self.repo.read_by_mail(mail):
            raise ExistsError

        username = self.generate_unique_username()
        user = User(
            mail=mail,
            password=password,
            username=username,
            display_name=username,
        )
        self.repo.create(user)
        return user

    def get_by_mail(self, mail: str) -> User:
        user = self.repo.read_by_mail(mail)
        if not user:
            raise DoesNotExistError
        return user

    def generate_unique_username(self) -> str:
        faker = Faker()
        username = faker.unique.user_name()
        while self.repo.read_by_username(username):
            username = faker.unique.user_name()
        return str(username)
