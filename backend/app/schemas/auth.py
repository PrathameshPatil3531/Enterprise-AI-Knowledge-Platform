"""
app/schemas/auth.py — Authentication Response Schemas

Defines the response shape for token endpoints.
"""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """
    Response returned by POST /auth/login and POST /auth/refresh.

    access_token: The JWT access token. Store in memory (NOT localStorage).
    token_type: Always "bearer" — the OAuth2 standard token type.

    Note: The refresh token is NOT in this response.
    It is set as an HTTP-only cookie by the server automatically.
    The client never reads, stores, or manages the refresh token.
    """

    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """
    Generic success message response.

    Used for operations that don't return data:
    - POST /auth/logout → {"message": "Successfully logged out"}
    - POST /auth/change-password → {"message": "Password changed successfully."}
    """

    message: str
