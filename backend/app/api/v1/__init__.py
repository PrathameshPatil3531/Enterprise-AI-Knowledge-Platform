from fastapi import APIRouter

# ---------------------------------------------------------------------------
# API v1 Router
#
# This is the aggregator router for all v1 endpoints.
# Sub-routers for each feature are included here as they are built.
#
# The prefix /api/v1 is applied in main.py:
#   app.include_router(v1_router, prefix="/api/v1")
#
# So a route defined as @router.get("/health") here becomes:
#   GET /api/v1/health
# ---------------------------------------------------------------------------
router = APIRouter()


@router.get("/health", tags=["System"])
async def api_health():
    """
    API v1 health check endpoint.

    Returns a simple JSON response confirming the API layer is reachable.
    Used by load balancers and monitoring tools to verify the service is up.

    This endpoint requires NO authentication — it must always be accessible.
    """
    return {"status": "ok", "version": "v1"}


# ---------------------------------------------------------------------------
# Future sub-routers — uncomment as each milestone is completed:
#
# from app.api.v1 import auth
# from app.api.v1 import organizations
# from app.api.v1 import documents
# from app.api.v1 import chat
# from app.api.v1 import admin
#
# router.include_router(auth.router,          prefix="/auth",          tags=["Authentication"])
# router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
# router.include_router(documents.router,     prefix="/documents",     tags=["Documents"])
# router.include_router(chat.router,          prefix="/chat",          tags=["Chat"])
# router.include_router(admin.router,         prefix="/admin",         tags=["Admin"])
# ---------------------------------------------------------------------------
