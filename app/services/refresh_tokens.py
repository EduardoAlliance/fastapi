import logging
from typing import Protocol

from redis.exceptions import RedisError

logger = logging.getLogger("app.auth.refresh_tokens")


class RedisLike(Protocol):
    def set(self, name: str, value: str, /, *, ex: int | None = None) -> object: ...

    def delete(self, *names: str) -> int: ...

    def exists(self, *names: str) -> int: ...


class RefreshTokenStore:
    """Registro en Redis de refresh tokens de un solo uso.

    Cada refresh token tiene un ``jti`` activo mientras no se haya usado. La
    rotación consume ese ``jti``; si vuelve a aparecer, se asume reutilización y
    se revoca toda la familia (``sid``) a la que pertenece el token.
    """

    def __init__(self, redis: RedisLike) -> None:
        self.redis = redis

    @staticmethod
    def _token_key(jti: str) -> str:
        return f"auth:refresh:token:{jti}"

    @staticmethod
    def _family_key(session_id: str) -> str:
        return f"auth:refresh:family:{session_id}"

    def register(self, jti: str, session_id: str, ttl_seconds: int) -> None:
        try:
            self.redis.set(self._token_key(jti), session_id, ex=max(ttl_seconds, 1))
        except RedisError:
            logger.warning("refresh_token_store_unavailable")

    def is_family_revoked(self, session_id: str) -> bool:
        try:
            return bool(self.redis.exists(self._family_key(session_id)))
        except RedisError:
            logger.warning("refresh_token_store_unavailable")
            return False

    def consume(self, jti: str) -> bool | None:
        """Elimina el jti activo de forma atómica.

        Devuelve ``True`` si estaba activo, ``False`` si ya se había usado o no
        existe y ``None`` si Redis no está disponible.
        """
        try:
            return bool(self.redis.delete(self._token_key(jti)))
        except RedisError:
            logger.warning("refresh_token_store_unavailable")
            return None

    def revoke_family(self, session_id: str, ttl_seconds: int) -> None:
        try:
            self.redis.set(
                self._family_key(session_id),
                "revoked",
                ex=max(ttl_seconds, 1),
            )
        except RedisError:
            logger.warning("refresh_token_store_unavailable")

    def revoke_token(self, jti: str) -> None:
        try:
            self.redis.delete(self._token_key(jti))
        except RedisError:
            logger.warning("refresh_token_store_unavailable")
