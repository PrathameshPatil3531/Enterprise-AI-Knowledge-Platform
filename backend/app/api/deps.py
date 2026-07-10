"""
app/api/deps.py — FastAPI Dependency Injection Hub

All shared FastAPI dependencies live here.
Route handlers import from deps.py exclusively — never from db.session or
repositories directly. This single import point makes testing trivial:

    # In tests — override the dependency to inject a mock user:
    app.dependency_overrides[get_current_user] = lambda: mock_user

Available dependencies:
    get_db              → Database session (one per request)
    get_current_user    → Authenticated User (from JWT Bearer token)

Future dependencies (added in later milestones):
    get_current_org     → Organization context (from user's membership)
    require_role(role)  → RBAC enforcement factory
"""

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException, BadRequestException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import user_repository

# ---------------------------------------------------------------------------
# HTTP Bearer Security Scheme
#
# Instructs FastAPI (and Swagger UI) that protected endpoints require
# Authorization: Bearer <token> in the request header.
#
# auto_error=False:
#   Do NOT automatically raise a 403 if the header is missing.
#   We raise an UnauthorizedException (401) ourselves with a clearer message.
#   FastAPI's default 403 for missing Bearer is confusing to API consumers.
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=False)

__all__ = ["get_db", "get_current_user"]


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — Validates JWT and returns the authenticated User.

    Flow:
        1. Extract Bearer token from the Authorization header
        2. Decode JWT: validate signature, expiry, and token type
        3. Extract user_id from the 'sub' claim
        4. Fetch the user from PostgreSQL
        5. Verify the user is still active (not deactivated after token was issued)
        6. Return the User ORM object to the route handler

    The route handler receives a fully validated, active User object.
    No route needs to re-validate the JWT or check user.is_active.

    Usage:
        from app.api.deps import get_current_user

        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": str(current_user.id)}

    Raises:
        UnauthorizedException (HTTP 401): On any validation failure.
    """
    if not credentials:
        raise UnauthorizedException(
            "Authorization header missing. "
            "Include 'Authorization: Bearer <access_token>' in your request."
        )

    token = credentials.credentials

    # decode_access_token validates signature, expiry, and token type.
    # Raises UnauthorizedException if anything is wrong.
    payload = decode_access_token(token)

    # Extract user_id from the 'sub' claim
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload is missing 'sub' claim")

    # Parse to UUID (guards against malformed token payloads)
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user ID format in token")

    # Fetch from DB — this also checks is_active=True
    # Why fetch from DB at all if JWT is self-contained?
    # → An admin may deactivate a user AFTER their token was issued.
    #   Without the DB check, a deactivated user can still use the API for 15 minutes.
    #   For most applications, this DB fetch is an acceptable cost.
    user = user_repository.get_by_id(db, user_id=user_id)

    if not user:
        # User was deleted or deactivated after the token was issued
        raise UnauthorizedException("User account not found or has been deactivated")

    return user


# ---------------------------------------------------------------------------
# Organization & RBAC Dependencies (Milestone 3)
# ---------------------------------------------------------------------------

from fastapi import Header, Path
from app.models.membership import Membership, Role
from app.models.organization import Organization
from app.repositories.membership_repository import membership_repository
from app.repositories.organization_repository import organization_repository
from app.core.exceptions import ForbiddenException, NotFoundException

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_org_membership",
    "require_owner",
    "require_admin",
    "require_member",
]

def get_current_org_membership(
    organization_id: uuid.UUID = Header(None, alias="X-Organization-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Membership:
    """
    Dependency that extracts the organization ID from the X-Organization-Id header
    and retrieves the user's membership for that organization.
    """
    if not organization_id:
        raise BadRequestException("Missing X-Organization-Id header")

    org = organization_repository.get_by_id(db, org_id=organization_id)
    if not org:
        raise NotFoundException("Organization not found")

    membership = membership_repository.get_by_user_and_org(
        db, user_id=current_user.id, org_id=organization_id
    )
    if not membership:
        raise ForbiddenException("You are not a member of this organization")

    return membership


def require_role(minimum_role: Role):
    """
    Factory dependency that enforces role-based access control.
    """
    role_hierarchy = {
        Role.VIEWER: 0,
        Role.MEMBER: 1,
        Role.ADMIN: 2,
        Role.OWNER: 3,
    }

    def dependency(
        membership: Membership = Depends(get_current_org_membership),
    ) -> Membership:
        if role_hierarchy.get(membership.role, -1) < role_hierarchy.get(minimum_role, 999):
            raise ForbiddenException(f"Requires role '{minimum_role.value}' or higher")
        return membership

    return dependency


# Reusable dependency aliases
require_owner = require_role(Role.OWNER)
require_admin = require_role(Role.ADMIN)
require_member = require_role(Role.MEMBER)

