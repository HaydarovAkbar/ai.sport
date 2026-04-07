import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if settings.DEBUG
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    SENSITIVE_PATHS = {"/api/v1/auth/login", "/api/v1/auth/refresh"}

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        log = logger.bind(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            client_ip=request.client.host if request.client else None,
        )

        if response.status_code >= 500:
            log.error("request_error")
        elif response.status_code >= 400:
            log.warning("request_warning")
        else:
            log.info("request")

        return response
