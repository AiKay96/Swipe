from dataclasses import dataclass

import bcrypt
from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError, ExistsError
from src.core.users import User
from src.infra.models.user import User as UserModel


@dataclass
class UserRepository:
    db: Session

    def create(self, user: User) -> None:
        if self.db.query(UserModel).filter_by(mail=user.mail).first():
            raise ExistsError

        db_user = UserModel(
            mail=user.mail,
            hashed_password=bcrypt.hashpw(
                user.password.encode(), bcrypt.gensalt()
            ).decode(),
            user_id=user.id,
        )
        self.db.add(db_user)
        self.db.commit()

    def read(self, mail: str) -> User:
        user = self.db.query(UserModel).filter_by(mail=mail).first()
        if not user:
            raise DoesNotExistError
        assert user.id is not None
        assert user.mail is not None
        assert user.hashed_password is not None

        return User(
            id=user.id,
            mail=user.mail,
            password=user.hashed_password,
        )
