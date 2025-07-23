from uuid import UUID

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.users import User as DomainUser
from src.runner.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("mail"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    mail: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)
    bio: Mapped[str | None] = mapped_column(String)

    def __init__(
        self,
        user_id: UUID,
        mail: str,
        hashed_password: str,
        username: str,
        display_name: str,
        bio: str | None = None,
    ) -> None:
        self.id = user_id
        self.mail = mail
        self.hashed_password = hashed_password
        self.username = username
        self.display_name = display_name
        self.bio = bio

    def to_object(self) -> DomainUser:
        return DomainUser(
            id=self.id,
            mail=self.mail,
            password=self.hashed_password,
            username=self.username,
            display_name=self.display_name,
            bio=self.bio,
        )
