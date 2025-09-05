from fastapi import WebSocket, status

from src.core.users import User
from src.infra.services.auth import AuthService


async def ws_get_current_user(ws: WebSocket) -> User:
    token = ws.query_params.get("token") or ""
    if not token:
        auth = ws.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()

    if not token:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        raise RuntimeError("No token")

    user_repo = ws.app.state.user
    token_repo = ws.app.state.tokens
    auth_service = AuthService(user_repo, token_repo)

    try:
        return auth_service.get_user_from_token(token)
    except Exception:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        raise RuntimeError("Invalid token") from None
