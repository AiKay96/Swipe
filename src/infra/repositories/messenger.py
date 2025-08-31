from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from src.core.errors import DoesNotExistError
from src.core.messenger import Chat as DomainChat
from src.core.messenger import ChatSummary
from src.core.messenger import Message as DomainMessage
from src.infra.models.messenger import Chat as ChatModel
from src.infra.models.messenger import Message as MessageModel


@dataclass
class ChatRepository:
    db: Session

    def _normalize_pair(self, u1: UUID, u2: UUID) -> tuple[UUID, UUID]:
        return (u1, u2) if str(u1) < str(u2) else (u2, u1)

    def get(self, chat_id: UUID) -> DomainChat | None:
        db_chat = self.db.query(ChatModel).filter_by(id=chat_id).first()
        return db_chat.to_object() if db_chat else None

    def get_by_pair(self, user_id: UUID, peer_id: UUID) -> DomainChat | None:
        a, b = self._normalize_pair(user_id, peer_id)
        db_chat = (
            self.db.query(ChatModel)
            .filter(ChatModel.user_a_id == a, ChatModel.user_b_id == b)
            .first()
        )
        return db_chat.to_object() if db_chat else None

    def get_or_create(self, user_id: UUID, peer_id: UUID) -> DomainChat:
        a, b = self._normalize_pair(user_id, peer_id)
        existing = (
            self.db.query(ChatModel)
            .filter(ChatModel.user_a_id == a, ChatModel.user_b_id == b)
            .first()
        )
        if existing:
            return existing.to_object()

        db_chat = ChatModel(user_a_id=a, user_b_id=b)
        self.db.add(db_chat)
        self.db.commit()
        self.db.refresh(db_chat)
        return db_chat.to_object()

    def update_last_message(
        self, chat_id: UUID, message_id: UUID, created_at: datetime
    ) -> None:
        chat = self.db.query(ChatModel).filter_by(id=chat_id).first()
        if not chat:
            raise DoesNotExistError("Chat not found.")
        chat.last_message_id = message_id
        chat.last_message_at = created_at
        self.db.commit()
        self.db.refresh(chat)

    def list_for_user(
        self, user_id: UUID, limit: int, before: datetime | None = None
    ) -> list[ChatSummary]:
        q = self.db.query(ChatModel).filter(
            or_(ChatModel.user_a_id == user_id, ChatModel.user_b_id == user_id)
        )

        if before:
            q = q.filter(
                or_(
                    ChatModel.last_message_at == None,  # noqa: E711
                    ChatModel.last_message_at < before,
                )
            )

        q = q.order_by(ChatModel.last_message_at.desc().nullslast()).limit(limit)
        chats: Sequence[ChatModel] = q.all()

        chat_ids = [c.id for c in chats]
        if not chat_ids:
            return []

        unread_q = (
            self.db.query(
                MessageModel.chat_id,
                func.count(MessageModel.id).label("cnt"),
            )
            .filter(MessageModel.chat_id.in_(chat_ids))
            .filter(MessageModel.sender_id != user_id)
            .filter(
                or_(
                    and_(
                        ChatModel.user_a_id == user_id,
                        MessageModel.seen_at_user_a.is_(None),
                    ),
                    and_(
                        ChatModel.user_b_id == user_id,
                        MessageModel.seen_at_user_b.is_(None),
                    ),
                )
            )
            .join(ChatModel, ChatModel.id == MessageModel.chat_id)
            .group_by(MessageModel.chat_id)
            .all()
        )
        unread_map: dict[UUID, int] = {row.chat_id: row.cnt for row in unread_q}

        last_ids = [c.last_message_id for c in chats if c.last_message_id]
        last_bodies: dict[UUID, str] = {}
        if last_ids:
            rows = (
                self.db.query(MessageModel.id, MessageModel.body)
                .filter(MessageModel.id.in_(last_ids))
                .all()
            )
            last_bodies = {r.id: r.body for r in rows}

        summaries: list[ChatSummary] = []
        for c in chats:
            peer_id = c.user_b_id if c.user_a_id == user_id else c.user_a_id
            last_body = (
                last_bodies.get(c.last_message_id) if c.last_message_id else None
            )
            summaries.append(
                ChatSummary(
                    chat=c.to_object(),
                    peer_id=peer_id,
                    unread_count=unread_map.get(c.id, 0),
                    last_body=last_body,
                )
            )
        return summaries


@dataclass
class MessageRepository:
    db: Session

    def create(self, chat_id: UUID, sender_id: UUID, body: str) -> DomainMessage:
        db_msg = MessageModel(chat_id=chat_id, sender_id=sender_id, body=body)
        self.db.add(db_msg)
        self.db.commit()
        self.db.refresh(db_msg)
        return db_msg.to_object()

    def list_by_chat(
        self, chat_id: UUID, limit: int, before: datetime | None = None
    ) -> list[DomainMessage]:
        q = self.db.query(MessageModel).filter(MessageModel.chat_id == chat_id)
        if before:
            q = q.filter(MessageModel.created_at < before)
        q = q.order_by(MessageModel.created_at.desc()).limit(limit)
        rows = q.all()
        return [m.to_object() for m in rows][::-1]

    def mark_seen_for_user(
        self, chat_id: UUID, user_id: UUID, up_to: datetime | None = None
    ) -> int:
        chat = self.db.query(ChatModel).filter_by(id=chat_id).first()
        if not chat:
            raise DoesNotExistError("Chat not found.")

        is_a = chat.user_a_id == user_id
        is_b = chat.user_b_id == user_id
        if not (is_a or is_b):
            raise DoesNotExistError("User not in chat.")

        q = self.db.query(MessageModel).filter(
            MessageModel.chat_id == chat_id,
            MessageModel.sender_id != user_id,
        )
        if up_to:
            q = q.filter(MessageModel.created_at <= up_to)

        now = datetime.utcnow()
        if is_a:
            updated = q.filter(MessageModel.seen_at_user_a.is_(None)).update(
                {MessageModel.seen_at_user_a: now}, synchronize_session=False
            )
        else:
            updated = q.filter(MessageModel.seen_at_user_b.is_(None)).update(
                {MessageModel.seen_at_user_b: now}, synchronize_session=False
            )

        self.db.commit()
        return int(updated)

    def unread_count(self, chat_id: UUID, user_id: UUID) -> int:
        chat = self.db.query(ChatModel).filter_by(id=chat_id).first()
        if not chat:
            raise DoesNotExistError("Chat not found.")
        is_a = chat.user_a_id == user_id
        is_b = chat.user_b_id == user_id
        if not (is_a or is_b):
            raise DoesNotExistError("User not in chat.")

        q = self.db.query(func.count(MessageModel.id)).filter(
            MessageModel.chat_id == chat_id,
            MessageModel.sender_id != user_id,
        )
        if is_a:
            q = q.filter(MessageModel.seen_at_user_a.is_(None))
        else:
            q = q.filter(MessageModel.seen_at_user_b.is_(None))
        return int(q.scalar() or 0)
