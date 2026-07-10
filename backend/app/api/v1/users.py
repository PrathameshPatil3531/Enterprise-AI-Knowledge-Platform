"""
app/api/v1/users.py — User Profile HTTP Route Handlers

Currently contains one endpoint: GET /users/me.
As the platform grows, this file will include:
    - PATCH /users/me     → Update profile (name, avatar)
    - DELETE /users/me    → Delete account (with confirmation)
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description=(
        "Return the authenticated user's profile.\n\n"
        "**Requires:** Valid JWT access token in `Authorization: Bearer <token>` header.\n\n"
        "The response includes id, email, full_name, verification status, and last login. "
        "The password hash is never included."
    ),
)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the currently authenticated user's profile.

    The `get_current_user` dependency handles all JWT validation.
    This route just returns the validated user object.

    - **200 OK**: Returns the user's profile.
    - **401 Unauthorized**: Missing or invalid access token.
    """
    return current_user
