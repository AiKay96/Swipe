from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class WSManager:
    def __init__(self) -> None:
        self._user_sockets: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._user_sockets[user_id].add(ws)

    def disconnect(self, user_id: UUID, ws: WebSocket) -> None:
        group = self._user_sockets.get(user_id)
        if group is None:
            return
        group.discard(ws)
        if not group:
            self._user_sockets.pop(user_id, None)

    async def send_to_user(self, user_id: UUID, payload: dict[str, Any]) -> None:
        for ws in list(self._user_sockets.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(user_id, ws)

    async def send_to_users(
        self, user_ids: list[UUID], payload: dict[str, Any]
    ) -> None:
        for uid in user_ids:
            await self.send_to_user(uid, payload)


manager = WSManager()
