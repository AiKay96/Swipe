from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.infra.models.token import Token


@dataclass
class TokenRepository:
    db: Session

    def save(self, jti: UUID, user_id: UUID, expires_at: datetime) -> None:
        token = Token(jti=jti, user_id=user_id, expires_at=expires_at)
        self.db.add(token)
        self.db.commit()

    def exists(self, jti: UUID) -> bool:
        return self.db.query(Token).filter_by(jti=jti).first() is not None

    def delete(self, jti: UUID) -> None:
        self.db.query(Token).filter_by(jti=jti).delete()
        self.db.commit()
