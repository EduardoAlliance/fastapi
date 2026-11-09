from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total de peticiones HTTP",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Duración de las peticiones HTTP en segundos",
    ["method", "path"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Peticiones HTTP en curso",
)


def observe_request(method: str, path: str, status: int, elapsed_seconds: float) -> None:
    REQUEST_COUNT.labels(method=method, path=path, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed_seconds)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
