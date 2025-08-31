from dataclasses import dataclass
from typing import Any
from uuid import UUID

import bcrypt
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError, ExistsError
from src.core.users import User
from src.infra.models.user import User as UserModel
from src.infra.models.user import User as UserORM


@dataclass
class UserRepository:
    db: Session

    def create(self, user: User) -> User:
        if self.db.query(UserModel).filter_by(mail=user.mail).first():
            raise ExistsError

        db_user = UserModel(
            mail=user.mail,
            hashed_password=bcrypt.hashpw(
                user.password.encode(), bcrypt.gensalt()
            ).decode(),
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user.to_object()

    def read_by(
        self,
        *,
        user_id: UUID | None = None,
        mail: str | None = None,
        username: str | None = None,
    ) -> User | None:
        query = self.db.query(UserModel)

        if user_id:
            user = query.filter_by(id=user_id).first()
        elif mail:
            user = query.filter_by(mail=mail).first()
        elif username:
            user = query.filter_by(username=username).first()

        if not user:
            return None

        return user.to_object()

    def read_many_by_ids(self, ids: list[UUID]) -> list[User]:
        if not ids:
            return []
        users = self.db.query(UserModel).filter(UserModel.id.in_(ids)).all()
        return [u.to_object() for u in users]

    def find_by_username(self, username: str) -> User | None:
        stmt = select(UserORM).where(UserORM.username.ilike(username))
        user = self.db.scalar(stmt)
        if not user:
            return None
        return user.to_object()

    def update(self, user_id: UUID, updates: dict[str, Any]) -> None:
        user = self.db.query(UserModel).filter_by(id=user_id).first()
        if not user:
            raise DoesNotExistError("User not found.")

        for field, value in updates.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)

    def search(self, query: str, limit: int = 10) -> list[User]:
        stmt = (
            select(UserORM)
            .where(
                or_(
                    UserORM.username.ilike(f"%{query}%"),
                    UserORM.display_name.ilike(f"%{query}%"),
                    func.similarity(UserORM.username, query) > 0.3,
                    func.similarity(UserORM.display_name, query) > 0.3,
                )
            )
            .order_by(
                func.greatest(
                    func.similarity(UserORM.username, query),
                    func.similarity(UserORM.display_name, query),
                ).desc()
            )
            .limit(limit)
        )
        rows = self.db.execute(stmt).scalars().all()
        return [u.to_object() for u in rows]
