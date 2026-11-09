import logging
from typing import Protocol

from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.exceptions import AppError

logger = logging.getLogger("app.rate_limit")


class RedisLike(Protocol):
    def incr(self, key: str, /) -> int: ...

    def expire(self, key: str, seconds: int, /) -> bool: ...


class RateLimiter:
    def __init__(self, redis: RedisLike, enabled: bool = True) -> None:
        self.redis = redis
        self.enabled = enabled

    def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        if not self.enabled:
            return True

        try:
            current = self.redis.incr(key)
            self.redis.expire(key, window_seconds)
        except RedisError:
            logger.warning("rate_limit_unavailable")
            return True

        return current <= limit


def enforce_login_rate_limit(
    limiter: RateLimiter,
    client_ip: str,
    email: str,
) -> None:
    settings = get_settings()
    window = settings.login_rate_limit_window_seconds

    checks = (
        (f"rate:login:ip:{client_ip}", settings.login_rate_limit_ip_attempts),
        (f"rate:login:email:{email.lower()}", settings.login_rate_limit_email_attempts),
    )

    for key, limit in checks:
        if not limiter.hit(key, limit, window):
            raise AppError(
                429,
                "rate_limit_exceeded",
                "Demasiados intentos de inicio de sesión",
                headers={"Retry-After": str(window)},
            )
