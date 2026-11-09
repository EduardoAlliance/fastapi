from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    session_id: str | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
        "jti": uuid4().hex,
    }
    if session_id is not None:
        payload["sid"] = session_id
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    session_id: str | None = None,
) -> str:
    return _create_token(
        subject,
        "access",
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes),
        session_id=session_id,
    )


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
    session_id: str | None = None,
) -> str:
    return _create_token(
        subject,
        "refresh",
        expires_delta or timedelta(days=settings.refresh_token_expire_days),
        session_id=session_id,
    )


def decode_token(token: str, *, verify_exp: bool = True) -> dict[str, Any]:
    options: Any = {"require": ["exp", "sub", "type"]}
    if not verify_exp:
        options["verify_exp"] = False
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        options=options,
    )
