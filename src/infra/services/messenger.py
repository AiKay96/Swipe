from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.core.errors import DoesNotExistError
from src.core.messenger import Chat, ChatSummary, Message
from src.infra.repositories.messenger import ChatRepository, MessageRepository


@dataclass
class MessengerService:
    chat_repo: ChatRepository
    message_repo: MessageRepository

    def get_or_start_chat(self, user_id: UUID, peer_id: UUID) -> Chat:
        return self.chat_repo.get_or_create(user_id, peer_id)

    def send_message(self, sender_id: UUID, peer_id: UUID, body: str) -> Message:
        chat = self.chat_repo.get_or_create(sender_id, peer_id)
        msg = self.message_repo.create(chat_id=chat.id, sender_id=sender_id, body=body)
        self.chat_repo.update_last_message(
            chat_id=chat.id, message_id=msg.id, created_at=msg.created_at
        )
        return msg

    def get_inbox(
        self,
        user_id: UUID,
        *,
        limit: int = 30,
        before: datetime | None = None,
    ) -> list[ChatSummary]:
        return self.chat_repo.list_for_user(user_id=user_id, limit=limit, before=before)

    def get_messages(
        self,
        user_id: UUID,
        peer_id: UUID | None = None,
        chat_id: UUID | None = None,
        *,
        limit: int = 50,
        before: datetime | None = None,
        mark_seen: bool = True,
    ) -> list[Message]:
        if not chat_id:
            if not peer_id:
                raise DoesNotExistError("Provide either chat_id or peer_id.")
            chat = self.chat_repo.get_or_create(user_id, peer_id)
            chat_id = chat.id
        else:
            get_chat = self.chat_repo.get(chat_id)
            if not get_chat:
                raise DoesNotExistError("Chat not found.")

        msgs = self.message_repo.list_by_chat(
            chat_id=chat_id, limit=limit, before=before
        )
        if mark_seen and msgs:
            self.message_repo.mark_seen_for_user(
                chat_id=chat_id, user_id=user_id, up_to=msgs[-1].created_at
            )
        return msgs

    def mark_chat_seen(self, user_id: UUID, chat_id: UUID) -> int:
        return self.message_repo.mark_seen_for_user(chat_id=chat_id, user_id=user_id)
