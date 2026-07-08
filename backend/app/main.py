"""
Enterprise AI Knowledge Platform — FastAPI Application Entry Point.

This module uses the Application Factory Pattern:
    app = create_app()

WHY a factory function instead of a module-level app?
    - Tests can call create_app() with different settings
    - Prevents side effects when the module is imported
    - Makes dependency injection overrides clean in tests
    - Industry standard pattern (Flask, Django use the same approach)

Entry point for Uvicorn:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging

# Configure logging before ANYTHING else.
# If this runs after other imports, some log messages get lost.
setup_logging()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — Startup and Shutdown Events
#
# The @asynccontextmanager lifespan is the modern FastAPI way to handle
# startup/shutdown logic (replaces the older @app.on_event("startup") approach).
#
# Code BEFORE yield → runs at startup
# Code AFTER yield  → runs at shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # ---- STARTUP ----
    logger.info("=" * 60)
    logger.info("  Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("  Environment : %s", settings.ENVIRONMENT)
    logger.info("  Debug mode  : %s", settings.DEBUG)
    logger.info("=" * 60)

    # Future startup tasks (added in later milestones):
    # - Verify database connection
    # - Verify Redis connection
    # - Load SentenceTransformer model into memory
    # - Ensure Qdrant collection exists

    yield  # Application runs here

    # ---- SHUTDOWN ----
    logger.info("Shutting down %s", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.

    This function is called once at module load time.
    During testing, you can call create_app() with mocked settings.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "A production-ready Enterprise AI Knowledge Platform. "
            "Upload documents, ask questions, get AI-powered answers with citations."
        ),
        # Swagger UI and ReDoc only exposed in development
        # In production, API docs should be behind authentication or disabled
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # Middleware Registration
    #
    # IMPORTANT: Middleware is applied in REVERSE order of registration.
    # The LAST middleware added runs FIRST on incoming requests.
    #
    # Execution order for a request:
    #   LoggingMiddleware → CORSMiddleware → Route Handler
    #
    # Execution order for a response:
    #   Route Handler → CORSMiddleware → LoggingMiddleware
    # ------------------------------------------------------------------

    # CORS — must be first so all responses (including errors) have CORS headers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,   # Required for cookies (refresh token)
        allow_methods=["*"],      # Allow GET, POST, PUT, DELETE, etc.
        allow_headers=["*"],      # Allow Authorization, Content-Type, etc.
    )

    # Request/response logging (runs after CORS in the middleware stack)
    from app.middleware.logging_middleware import LoggingMiddleware
    app.add_middleware(LoggingMiddleware)

    # ------------------------------------------------------------------
    # Router Registration
    # ------------------------------------------------------------------
    from app.api.v1 import router as v1_router
    app.include_router(v1_router, prefix="/api/v1")

    # ------------------------------------------------------------------
    # Root Health Check
    #
    # This endpoint lives at the root (not /api/v1/) so that:
    # - Docker health checks can hit it without API versioning
    # - Load balancers (AWS ALB, Nginx) can monitor it simply
    # - It's always available regardless of API version changes
    # ------------------------------------------------------------------
    @app.get("/health", tags=["System"], include_in_schema=False)
    async def health_check():
        """Root health check — used by Docker and load balancers."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    return app


# ---------------------------------------------------------------------------
# Create the application instance.
# Uvicorn runs: uvicorn app.main:app
# ---------------------------------------------------------------------------
app = create_app()
