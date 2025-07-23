from datetime import datetime
from typing import Protocol
from uuid import UUID


class TokenRepository(Protocol):
    def save(self, jti: UUID, user_id: UUID, expires_at: datetime) -> None:
        pass

    def exists(self, jti: UUID) -> bool:
        pass

    def delete(self, jti: UUID) -> None:
        pass
