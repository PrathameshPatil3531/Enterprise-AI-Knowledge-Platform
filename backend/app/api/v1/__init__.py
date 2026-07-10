"""
app/api/v1/__init__.py — API v1 Router Aggregator

This router is the single entry point for all v1 endpoints.
It is included in main.py with prefix="/api/v1".

To add a new feature router:
    1. Create app/api/v1/my_feature.py with a router = APIRouter()
    2. Import it here and call router.include_router(...)
"""

from fastapi import APIRouter

from app.api.v1 import auth, users

router = APIRouter()

# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------
@router.get("/health", tags=["System"], include_in_schema=False)
async def api_v1_health():
    """API v1 health check — always public, no auth required."""
    return {"status": "ok", "version": "v1"}


# ---------------------------------------------------------------------------
# Milestone 2 — Identity & Access Management
# ---------------------------------------------------------------------------
router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

# ---------------------------------------------------------------------------
# Future milestones (uncomment as implemented):
# ---------------------------------------------------------------------------
# from app.api.v1 import organizations, documents, chat, admin
#
# router.include_router(
#     organizations.router,
#     prefix="/organizations",
#     tags=["Organizations"],
# )
# router.include_router(
#     documents.router,
#     prefix="/documents",
#     tags=["Documents"],
# )
# router.include_router(
#     chat.router,
#     prefix="/chat",
#     tags=["Chat"],
# )
# router.include_router(
#     admin.router,
#     prefix="/admin",
#     tags=["Admin"],
# )
