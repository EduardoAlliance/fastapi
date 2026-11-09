from redis.exceptions import RedisError

from app.core.config import get_settings
from app.services.rate_limit import RateLimiter
from tests.helpers import login_user, register_user


class FakeRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key: str, seconds: int) -> bool:
        self.ttls[key] = seconds
        return True


class BrokenRedis:
    def incr(self, key: str) -> int:
        raise RedisError("redis unavailable")

    def expire(self, key: str, seconds: int) -> bool:
        return True


def test_rate_limiter_allows_under_limit():
    redis = FakeRedis()
    limiter = RateLimiter(redis)

    assert limiter.hit("key", 2, 60) is True
    assert limiter.hit("key", 2, 60) is True
    assert limiter.hit("key", 2, 60) is False
    assert redis.ttls["key"] == 60


def test_rate_limiter_disabled():
    redis = FakeRedis()
    limiter = RateLimiter(redis, enabled=False)

    assert limiter.hit("key", 1, 60) is True
    assert redis.counts == {}


def test_rate_limiter_fails_open_when_redis_is_unavailable():
    limiter = RateLimiter(BrokenRedis())

    assert limiter.hit("key", 1, 60) is True


def test_login_rate_limit_exceeded(client, rate_limiter):
    rate_limiter.allowed = False

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "secreto123"},
    )

    assert response.status_code == 429
    body = response.json()
    assert body["error"]["code"] == "rate_limit_exceeded"
    assert response.headers["Retry-After"] == str(get_settings().login_rate_limit_window_seconds)
    assert rate_limiter.calls


def test_login_rate_limit_checks_ip_and_email(client, rate_limiter):
    register_user(client, "ana@example.com")

    response = login_user(client, "ana@example.com")

    assert response.status_code == 200
    keys = [call[0] for call in rate_limiter.calls]
    assert any(key.startswith("rate:login:ip:") for key in keys)
    assert "rate:login:email:ana@example.com" in keys
