import pytest
from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # registra los modelos en Base.metadata
from app.api.deps import get_rate_limiter
from app.core.redis import get_redis
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


class FakeRateLimiter:
    def __init__(self) -> None:
        self.allowed = True
        self.calls: list[tuple[str, int, int]] = []

    def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        self.calls.append((key, limit, window_seconds))
        return self.allowed


class FakeRedis:
    def __init__(self) -> None:
        self.available = True
        self.data: dict[str, str] = {}

    def _ensure_available(self) -> None:
        if not self.available:
            raise RedisError("redis unavailable")

    def ping(self) -> bool:
        self._ensure_available()
        return True

    def set(self, name: str, value: str, *, ex: int | None = None) -> bool:
        self._ensure_available()
        self.data[name] = value
        return True

    def delete(self, *names: str) -> int:
        self._ensure_available()
        return sum(1 for name in names if self.data.pop(name, None) is not None)

    def exists(self, *names: str) -> int:
        self._ensure_available()
        return sum(1 for name in names if name in self.data)


@pytest.fixture
def db():
    with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def rate_limiter() -> FakeRateLimiter:
    return FakeRateLimiter()


@pytest.fixture
def redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def client(db, rate_limiter, redis):
    def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_rate_limiter] = lambda: rate_limiter
    fastapi_app.dependency_overrides[get_redis] = lambda: redis
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
