from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.main import app as fastapi_app


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_health_preserves_request_id(client):
    response = client.get(
        "/health",
        headers={"X-Request-ID": "test-request-id"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"


def test_readiness_reports_healthy_dependencies(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "redis": "ok"},
    }


def test_readiness_is_degraded_when_redis_is_unavailable(client, redis):
    redis.available = False

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "checks": {"database": "ok", "redis": "unavailable"},
    }


class BrokenSession:
    def execute(self, *args: object, **kwargs: object) -> None:
        raise SQLAlchemyError("database down")


def test_readiness_is_unavailable_when_database_fails(client):
    fastapi_app.dependency_overrides[get_db] = lambda: BrokenSession()

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "checks": {"database": "unavailable", "redis": "ok"},
    }


def test_metrics_exposes_prometheus_format(client):
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert 'path="/health"' in response.text
