import logging
import sys


def setup_logging() -> None:
    """
    Configure application-wide logging.

    WHY structured logging matters:
    - In production, logs are collected by Datadog / CloudWatch / ELK
    - Structured format (consistent fields) allows automated parsing
    - request_id field enables tracing a single request across many log lines

    WHY stdout (not a file):
    - Docker collects stdout automatically via `docker logs`
    - Cloud platforms (AWS, GCP) capture stdout for their log services
    - No disk I/O, no log rotation needed at the app level

    Call this function ONCE before creating the FastAPI app.
    """
    from app.core.config import settings

    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Log format:
    # 2024-01-15 14:32:01 | INFO     | app.api.v1.auth:42 | User logged in
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Guard: prevent duplicate handlers if setup_logging() is called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # -------------------------------------------------------------------------
    # Suppress noisy third-party libraries in production
    # These libraries emit many DEBUG-level lines that add noise without value
    # -------------------------------------------------------------------------
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a specific module.

    Usage (in every module that needs logging):
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Document uploaded: %s", document_id)

    Using __name__ as the logger name means log lines will show
    the full module path (e.g., app.services.document_service:87)
    making it easy to find the source of any log message.
    """
    return logging.getLogger(name)
