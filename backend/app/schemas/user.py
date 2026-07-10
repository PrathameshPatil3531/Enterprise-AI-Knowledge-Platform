"""
app/schemas/user.py — User Pydantic Schemas (DTOs)

These schemas define the data shape for:
- User registration input validation
- Login input validation
- User data returned in API responses
- Password change requests

RULE: NEVER return a SQLAlchemy User model directly from an endpoint.
      Always return a UserResponse (or similar) schema.
      This prevents accidentally exposing password_hash or internal fields.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """
    Schema for POST /auth/register request body.

    EmailStr: Pydantic validates that the string is a valid email format.
              Requires `email-validator` package to be installed.

    Password constraints (validated in field_validator below):
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """

    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Must be 8+ characters with uppercase, lowercase, and digit.",
    )
    full_name: str | None = Field(
        None,
        max_length=255,
        description="Optional display name.",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Enforce password complexity rules.

        Why these rules?
        - Uppercase + lowercase: prevents all-lowercase dictionary words
        - Digit: prevents purely alphabetic passwords
        - 8+ chars: prevents short brute-forceable passwords

        Note: bcrypt will handle the actual security. These rules are
        UX guidance — they reduce obvious weak passwords.
        """
        errors = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if errors:
            raise ValueError(f"Password must contain {', '.join(errors)}")
        return v


class UserLogin(BaseModel):
    """Schema for POST /auth/login request body."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Schema for User data returned in API responses.

    IMPORTANT: password_hash is intentionally EXCLUDED.
    This is the public-safe representation of a User.

    model_config from_attributes=True:
        Allows Pydantic to read data from a SQLAlchemy User ORM object.
        Without this, Pydantic would only accept dicts.
        With this, `UserResponse.model_validate(user_orm_object)` works.
    """

    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    last_login: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    """Schema for POST /auth/change-password request body."""

    current_password: str = Field(..., description="The user's existing password.")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="The new password. Must meet complexity requirements.",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        errors = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if errors:
            raise ValueError(f"Password must contain {', '.join(errors)}")
        return v
