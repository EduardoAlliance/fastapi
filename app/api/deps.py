from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.services.rate_limit import RateLimiter
from app.services.refresh_tokens import RefreshTokenStore

SessionDep = Annotated[Session, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]

bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized(code: str, message: str) -> AppError:
    return AppError(
        status_code=401,
        code=code,
        message=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise unauthorized("not_authenticated", "Falta el token de acceso")

    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise unauthorized("token_expired", "El token ha expirado") from None
    except jwt.InvalidTokenError:
        raise unauthorized("invalid_token", "Token inválido") from None

    if payload.get("type") != "access":
        raise unauthorized("invalid_token", "Tipo de token inválido")

    subject = payload.get("sub")
    if subject is None or not str(subject).isdigit():
        raise unauthorized("invalid_token", "Token inválido")

    user = db.get(User, int(subject))
    if user is None:
        raise unauthorized("invalid_token", "Usuario no encontrado")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_user(current_user: CurrentUser) -> User:
    if not current_user.is_active:
        raise AppError(403, "inactive_user", "La cuenta está desactivada")
    return current_user


ActiveUser = Annotated[User, Depends(get_current_active_user)]


def require_superuser(current_user: ActiveUser) -> User:
    if not current_user.is_superuser:
        raise AppError(403, "forbidden", "No tienes permisos para esta acción")
    return current_user


SuperuserDep = Annotated[User, Depends(require_superuser)]


def get_rate_limiter(redis: RedisDep) -> RateLimiter:
    return RateLimiter(redis, enabled=get_settings().rate_limit_enabled)


RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]


def get_refresh_token_store(redis: RedisDep) -> RefreshTokenStore:
    return RefreshTokenStore(redis)


RefreshTokenStoreDep = Annotated[RefreshTokenStore, Depends(get_refresh_token_store)]
