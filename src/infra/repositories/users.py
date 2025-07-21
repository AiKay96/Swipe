from dataclasses import dataclass

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import ExistsError
from src.core.users import User
from src.infra.models.user import User as UserModel
from src.infra.models.user import User as UserORM


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
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
        )
        self.db.add(db_user)
        self.db.commit()

    def read_by_mail(self, mail: str) -> User | None:
        user = self.db.query(UserModel).filter_by(mail=mail).first()
        if not user:
            return None

        return User(
            id=user.id,
            mail=user.mail,
            password=user.hashed_password,
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
        )

    def read_by_username(self, username: str) -> User | None:
        stmt = select(UserORM).where(UserORM.username.ilike(username))
        user = self.db.scalar(stmt)
        if not user:
            return None
        return User(
            id=user.id,
            mail=user.mail,
            password=user.hashed_password,
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
        )
