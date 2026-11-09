import logging
from datetime import UTC, datetime
from uuid import uuid4

import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse
from app.services.refresh_tokens import RefreshTokenStore

logger = logging.getLogger("app.auth")


class AuthService:
    def __init__(self, db: Session, tokens: RefreshTokenStore) -> None:
        self.repository = UserRepository(db)
        self.tokens = tokens

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.repository.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise AppError(
                status_code=401,
                code="invalid_credentials",
                message="Email o contraseña incorrectos",
            )

        if not user.is_active:
            raise AppError(
                status_code=403,
                code="inactive_user",
                message="La cuenta está desactivada",
            )

        return self._issue_tokens(user)

    def refresh(self, refresh_token: str) -> TokenResponse:
        payload = self._decode_refresh(refresh_token)
        user_id, jti, session_id = self._token_identity(payload)

        if self.tokens.is_family_revoked(session_id):
            raise AppError(401, "token_revoked", "La sesión fue cerrada")

        consumed = self.tokens.consume(jti)
        if consumed is False:
            self.tokens.revoke_family(session_id, self._family_ttl())
            logger.warning(
                "refresh_token_reuse_detected user_id=%s session_id=%s jti=%s",
                user_id,
                session_id,
                jti,
            )
            raise AppError(
                401,
                "token_reused",
                "El refresh token ya fue utilizado; inicia sesión de nuevo",
            )

        user = self.repository.get(user_id)
        if user is None:
            raise AppError(401, "invalid_token", "Usuario no encontrado")

        if not user.is_active:
            raise AppError(403, "inactive_user", "La cuenta está desactivada")

        return self._issue_tokens(user, session_id=session_id)

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, verify_exp=False)
        except jwt.InvalidTokenError:
            raise AppError(401, "invalid_token", "Token inválido") from None

        if payload.get("type") != "refresh":
            raise AppError(401, "invalid_token", "Tipo de token inválido")

        jti = payload.get("jti")
        session_id = payload.get("sid")

        if isinstance(jti, str):
            self.tokens.revoke_token(jti)

        if isinstance(session_id, str):
            self.tokens.revoke_family(session_id, self._family_ttl())

    def _decode_refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise AppError(401, "token_expired", "El token ha expirado") from None
        except jwt.InvalidTokenError:
            raise AppError(401, "invalid_token", "Token inválido") from None

        if payload.get("type") != "refresh":
            raise AppError(401, "invalid_token", "Tipo de token inválido")

        return payload

    @staticmethod
    def _token_identity(payload: dict) -> tuple[int, str, str]:
        subject = payload.get("sub")
        jti = payload.get("jti")
        session_id = payload.get("sid")

        if (
            subject is None
            or not str(subject).isdigit()
            or not isinstance(jti, str)
            or not isinstance(session_id, str)
        ):
            raise AppError(401, "invalid_token", "Token inválido")

        return int(subject), jti, session_id

    def _issue_tokens(self, user: User, session_id: str | None = None) -> TokenResponse:
        settings = get_settings()
        session_id = session_id or uuid4().hex

        access_token = create_access_token(
            subject=str(user.id),
            session_id=session_id,
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            session_id=session_id,
        )

        payload = decode_token(refresh_token)
        self.tokens.register(
            jti=str(payload["jti"]),
            session_id=session_id,
            ttl_seconds=self._remaining_ttl(payload),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    @staticmethod
    def _family_ttl() -> int:
        return get_settings().refresh_token_expire_days * 24 * 60 * 60

    def _remaining_ttl(self, payload: dict) -> int:
        expires_at = payload.get("exp")
        if isinstance(expires_at, int | float):
            remaining = int(expires_at - datetime.now(UTC).timestamp())
            return max(remaining, 1)
        return self._family_ttl()
