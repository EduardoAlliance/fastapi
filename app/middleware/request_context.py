import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx
from app.core.metrics import REQUESTS_IN_PROGRESS, observe_request

logger = logging.getLogger("app.request")


def _route_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return str(path) if path else "unmatched"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = (request.headers.get("X-Request-ID") or str(uuid.uuid4()))[:100]
        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)

        start = time.perf_counter()
        REQUESTS_IN_PROGRESS.inc()
        try:
            response = await call_next(request)
            elapsed = time.perf_counter() - start
            elapsed_ms = elapsed * 1000

            observe_request(
                method=request.method,
                path=_route_path(request),
                status=response.status_code,
                elapsed_seconds=elapsed,
            )

            logger.info(
                "%s %s %s %.2fms",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
            return response
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s failed after %.2fms",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise
        finally:
            REQUESTS_IN_PROGRESS.dec()
            request_id_ctx.reset(token)
