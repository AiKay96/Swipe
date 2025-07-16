from uuid import UUID

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.runner.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("mail"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    mail: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, user_id: UUID, mail: str, hashed_password: str) -> None:
        self.id = user_id
        self.mail = mail
        self.hashed_password = hashed_password
