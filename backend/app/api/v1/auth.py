"""
app/api/v1/auth.py — Authentication HTTP Route Handlers

These are thin controllers. Each route:
    1. Reads request data (auto-validated by Pydantic)
    2. Calls the auth_service
    3. Sets/clears cookies as needed
    4. Returns the appropriate response schema

NO business logic here. All business rules live in AuthService.
"""

import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import BadRequestException
from app.models.user import User
from app.schemas.auth import MessageResponse, TokenResponse
from app.schemas.user import ChangePasswordRequest, UserCreate, UserLogin, UserResponse
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Cookie Configuration
#
# REFRESH_TOKEN_COOKIE_NAME: The name of the HTTP-only cookie.
# path="/api/v1/auth": IMPORTANT — the browser only sends this cookie
#   when making requests to /api/v1/auth/* paths.
#   This limits the cookie's exposure surface area.
#   A request to /api/v1/documents will NOT include the refresh token cookie.
# ---------------------------------------------------------------------------
_REFRESH_COOKIE_NAME = "refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    """
    Set the refresh token as an HTTP-only cookie.

    Security attributes explained:
    - httponly=True     → Not accessible via JavaScript (document.cookie).
                          XSS attacks cannot steal this token.
    - secure=True (prod)→ Cookie only transmitted over HTTPS.
                          In development (DEBUG=True), allows HTTP for localhost.
    - samesite="lax"   → Cookie is sent on same-site requests AND top-level cross-site
                          navigations (clicking a link), but NOT on cross-site sub-requests
                          (e.g., an img or form in a foreign page). Prevents CSRF.
    - path=...          → Cookie only sent to /api/v1/auth/* endpoints.
    - max_age           → Browser deletes cookie after this many seconds.
    """
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=not settings.DEBUG,   # True in production, False in development
        samesite="lax",
        path=_REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """
    Delete the refresh token cookie from the client browser.
    Used on logout and password change.
    """
    response.delete_cookie(
        key=_REFRESH_COOKIE_NAME,
        path=_REFRESH_COOKIE_PATH,
    )


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user",
    description=(
        "Create a new user account.\n\n"
        "**Password requirements:** Minimum 8 characters with at least one uppercase "
        "letter, one lowercase letter, and one digit.\n\n"
        "Returns the created user profile (no password)."
    ),
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """
    Register a new user account.

    - **201 Created**: User successfully registered.
    - **409 Conflict**: Email address already registered.
    - **422 Unprocessable Entity**: Validation error (weak password, invalid email).
    """
    return auth_service.register(db, user_data=user_data)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description=(
        "Authenticate with email and password.\n\n"
        "**Returns:** JWT access token in the response body.\n\n"
        "**Sets:** Refresh token as an HTTP-only cookie (not visible to JavaScript).\n\n"
        "Store the `access_token` in memory (React state) — NOT in localStorage."
    ),
)
def login(
    credentials: UserLogin,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate a user and issue JWT + refresh token.

    - **200 OK**: Login successful. Access token in body, refresh token in cookie.
    - **401 Unauthorized**: Invalid email or password.
    - **401 Unauthorized**: Account deactivated.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    _user, access_token, raw_refresh_token = auth_service.login(
        db,
        email=credentials.email,
        password=credentials.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    _set_refresh_cookie(response, raw_refresh_token)

    return TokenResponse(access_token=access_token)


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description=(
        "Exchange the refresh token cookie for a new access token.\n\n"
        "**Token Rotation:** The old refresh token is revoked and a new one is issued.\n\n"
        "**Reuse Detection:** If a revoked token is presented, all sessions are invalidated.\n\n"
        "The refresh token cookie is automatically included by the browser."
    ),
)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Refresh the access token using the HTTP-only refresh token cookie.

    - **200 OK**: New access token issued, new refresh token cookie set.
    - **400 Bad Request**: Refresh token cookie not present.
    - **401 Unauthorized**: Token invalid, revoked, expired.
    """
    raw_refresh_token = request.cookies.get(_REFRESH_COOKIE_NAME)

    if not raw_refresh_token:
        raise BadRequestException(
            "Refresh token cookie not found. Please log in again."
        )

    new_access_token, new_raw_refresh_token = auth_service.refresh(
        db,
        raw_refresh_token=raw_refresh_token,
    )

    # Set the new refresh token cookie (rotation complete)
    _set_refresh_cookie(response, new_raw_refresh_token)

    return TokenResponse(access_token=new_access_token)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout (current device)",
    description=(
        "Revoke the current refresh token and clear the cookie.\n\n"
        "The access token will expire naturally after 15 minutes.\n\n"
        "No Authorization header required — the refresh cookie identifies the session."
    ),
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Log out from the current device.

    - **200 OK**: Logged out successfully.
    """
    raw_refresh_token = request.cookies.get(_REFRESH_COOKIE_NAME)

    if raw_refresh_token:
        auth_service.logout(db, raw_refresh_token=raw_refresh_token)

    _clear_refresh_cookie(response)

    return MessageResponse(message="Successfully logged out")


# ---------------------------------------------------------------------------
# POST /auth/logout-all
# ---------------------------------------------------------------------------
@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout all devices",
    description=(
        "Revoke ALL active refresh tokens for the current user.\n\n"
        "Forces re-authentication on every device where the user is logged in.\n\n"
        "**Requires:** Valid access token in Authorization header."
    ),
)
def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Log out from all devices.

    - **200 OK**: All sessions terminated.
    - **401 Unauthorized**: Access token missing or invalid.
    """
    count = auth_service.logout_all(db, user_id=current_user.id)
    _clear_refresh_cookie(response)
    return MessageResponse(message=f"Logged out from {count} active session(s)")


# ---------------------------------------------------------------------------
# POST /auth/change-password
# ---------------------------------------------------------------------------
@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description=(
        "Change the authenticated user's password.\n\n"
        "**Requires:** Current password verification.\n\n"
        "**Effect:** All active sessions are revoked after password change — "
        "the user must log in again on all devices.\n\n"
        "**Requires:** Valid access token in Authorization header."
    ),
)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Change user password. All sessions are revoked after success.

    - **200 OK**: Password changed. All sessions terminated.
    - **400 Bad Request**: New password same as current.
    - **401 Unauthorized**: Current password incorrect.
    """
    auth_service.change_password(
        db,
        user_id=current_user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    _clear_refresh_cookie(response)
    return MessageResponse(
        message="Password changed successfully. Please log in again on all devices."
    )
