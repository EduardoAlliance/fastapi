import logging

from fastapi import APIRouter, status
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse, Response

from app.api.deps import RedisDep, SessionDep
from app.core.metrics import metrics_response

logger = logging.getLogger("app.health")

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: SessionDep, redis: RedisDep) -> Response:
    checks = {"database": "ok", "redis": "ok"}
    http_status = status.HTTP_200_OK

    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("readiness_database_failed")
        checks["database"] = "unavailable"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        redis.ping()
    except RedisError:
        logger.warning("readiness_redis_unavailable")
        checks["redis"] = "unavailable"

    if http_status != status.HTTP_200_OK:
        overall = "unavailable"
    elif "unavailable" in checks.values():
        overall = "degraded"
    else:
        overall = "ok"

    return JSONResponse(
        status_code=http_status,
        content={"status": overall, "checks": checks},
    )


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return metrics_response()
