import time
import logging
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Paths excluded from request logging to reduce noise in logs
_SKIP_PATHS = frozenset({"/health", "/favicon.ico", "/api/openapi.json"})


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP request/response logging middleware.

    For every request this middleware:
    1. Generates a unique request_id (UUID4)
    2. Attaches it to request.state so any route/service can reference it
    3. Logs the incoming request (method, path, client IP)
    4. Calls the next handler (actual route)
    5. Logs the outgoing response (status code, duration in ms)
    6. Adds X-Request-ID header to the response

    WHY X-Request-ID header?
    - Frontend receives this header and can log it
    - If a user reports a bug, they share this ID
    - You grep your logs for that ID to see the exact request/response chain
    - This is called "distributed tracing" at the simplest level

    WHY middleware instead of decorators on each route?
    - DRY: write once, applies to ALL routes automatically
    - AOP (Aspect-Oriented Programming): cross-cutting concern separated from business logic
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for health checks and static requests
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        # Generate unique ID for this request
        request_id = str(uuid4())
        request.state.request_id = request_id

        client_ip = request.client.host if request.client else "unknown"
        start_time = time.perf_counter()

        logger.info(
            "→ REQUEST  | id=%-36s | %s %s | ip=%s",
            request_id,
            request.method,
            request.url.path,
            client_ip,
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "✗ ERROR    | id=%-36s | %s %s | %.2fms | %s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                str(exc),
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "← RESPONSE | id=%-36s | %s %s | status=%d | %.2fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        # Attach request ID to response so clients can correlate logs
        response.headers["X-Request-ID"] = request_id
        return response
