from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core.messenger import ChatSummary, Message
from src.core.users import User
from src.infra.fastapi.dependables import MessengerServiceDependable, get_current_user
from src.infra.fastapi.utils import exception_response

messenger_api = APIRouter(tags=["Messenger"])


class MessageItem(BaseModel):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    body: str
    created_at: datetime
    seen_at_user_a: datetime | None
    seen_at_user_b: datetime | None

    @classmethod
    def from_message(cls, m: Message) -> "MessageItem":
        return cls(
            id=m.id,
            chat_id=m.chat_id,
            sender_id=m.sender_id,
            body=m.body,
            created_at=m.created_at,
            seen_at_user_a=m.seen_at_user_a,
            seen_at_user_b=m.seen_at_user_b,
        )


class ChatSummaryItem(BaseModel):
    chat_id: UUID
    peer_id: UUID
    last_message_at: datetime | None
    last_message_id: UUID | None
    last_body: str | None
    unread_count: int

    @classmethod
    def from_summary(cls, s: ChatSummary) -> "ChatSummaryItem":
        return cls(
            chat_id=s.chat.id,
            peer_id=s.peer_id,
            last_message_at=s.chat.last_message_at,
            last_message_id=s.chat.last_message_id,
            last_body=s.last_body,
            unread_count=s.unread_count,
        )


class InboxResponse(BaseModel):
    chats: list[ChatSummaryItem]


class MessagesResponse(BaseModel):
    messages: list[MessageItem]


class SendMessageResponse(BaseModel):
    message: MessageItem


class MarkSeenResponse(BaseModel):
    updated: int


@messenger_api.get("/inbox", response_model=InboxResponse, status_code=200)
def get_inbox(
    service: MessengerServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
    limit: int = Query(30, ge=1, le=100),
    before: datetime | None = None,
) -> dict[str, Any] | JSONResponse:
    try:
        items = service.get_inbox(user_id=user.id, limit=limit, before=before)
        return {"chats": [ChatSummaryItem.from_summary(s) for s in items]}
    except Exception as e:
        return exception_response(e)


@messenger_api.get("/messages", response_model=MessagesResponse, status_code=200)
def get_messages(
    service: MessengerServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
    peer_id: UUID | None = None,
    chat_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    before: datetime | None = None,
) -> dict[str, Any] | JSONResponse:
    try:
        msgs = service.get_messages(
            user_id=user.id,
            peer_id=peer_id,
            chat_id=chat_id,
            limit=limit,
            before=before,
        )
        return {"messages": [MessageItem.from_message(m) for m in msgs]}
    except Exception as e:
        return exception_response(e)


@messenger_api.post(
    "/messages/send", response_model=SendMessageResponse, status_code=201
)
def send_message(
    *,
    peer_id: UUID,
    body: str,
    service: MessengerServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        if body.strip():
            return exception_response(Exception("Message body cannot be empty."))
        msg = service.send_message(sender_id=user.id, peer_id=peer_id, body=body)
        return {"message": MessageItem.from_message(msg)}
    except Exception as e:
        return exception_response(e)


@messenger_api.post(
    "/chats/{chat_id}/seen", response_model=MarkSeenResponse, status_code=200
)
def mark_seen(
    chat_id: UUID,
    service: MessengerServiceDependable,
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any] | JSONResponse:
    try:
        updated = service.mark_chat_seen(user_id=user.id, chat_id=chat_id)
        return {"updated": updated}
    except Exception as e:
        return exception_response(e)
