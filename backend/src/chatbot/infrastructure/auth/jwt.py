from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from chatbot.domain.exceptions import AuthError


def create_access_token(
    *,
    user_id: int,
    secret_key: str,
    algorithm: str,
    expire_minutes: int,
) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str, *, secret_key: str, algorithm: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret_key, algorithms=[algorithm])
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid or expired access token.") from exc
