"""
app/models/refresh_token.py — Refresh Token ORM Model

Maps the `refresh_tokens` table in PostgreSQL.

Design decisions:
- Stores SHA-256 hash of token, never the raw token.
- is_revoked flag: allows instant revocation without row deletion.
- ip_address + user_agent: security audit trail.
- ForeignKey with ondelete="CASCADE": DB-level cleanup if user row is deleted directly.
- One user can have multiple active refresh tokens (multiple devices).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefreshToken(Base):
    """
    Represents a stateful refresh token stored in the database.

    Unlike access tokens (stateless JWTs), refresh tokens MUST be stored
    in the database so they can be revoked (on logout, password change, theft).

    Token Rotation Strategy:
        Every time a refresh token is used to get a new access token,
        the old refresh token is revoked and a new one is issued.
        This means a stolen token can only be used once before detection.
    """

    __tablename__ = "refresh_tokens"

    # --------------------------------------------------------------------------
    # Primary Key
    # --------------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # --------------------------------------------------------------------------
    # Foreign Key → users.id
    #
    # ondelete="CASCADE": If the parent User row is deleted at the database level
    # (not via ORM), all their refresh tokens are automatically deleted.
    # This prevents orphaned tokens if a user account is force-deleted.
    #
    # index=True: Fast lookup of "all tokens for user X" (used in logout_all)
    # --------------------------------------------------------------------------
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------------------------
    # Token Hash
    #
    # Stores the SHA-256 hash of the raw refresh token.
    # The raw token is ONLY ever seen by the client (in the HTTP-only cookie).
    #
    # unique=True: No two active tokens can have the same hash.
    # index=True:  Enables fast lookup during token validation (called on every refresh).
    # --------------------------------------------------------------------------
    token_hash: Mapped[str] = mapped_column(
        String(64),   # SHA-256 output is always 64 hex characters
        unique=True,
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------------------------
    # Expiration Timestamp
    #
    # Set to created_at + REFRESH_TOKEN_EXPIRE_DAYS (7 days by default).
    # The application checks this before accepting the token.
    # --------------------------------------------------------------------------
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # --------------------------------------------------------------------------
    # Revocation Flag
    #
    # True when the token has been explicitly invalidated:
    # - User logged out (single device)
    # - User logged out all devices
    # - User changed password
    # - Security system detected token reuse (possible theft)
    #
    # WHY not delete revoked tokens?
    # Keeping revoked tokens allows detecting token reuse attacks:
    # If a revoked token is presented again, we know it may have been stolen.
    # --------------------------------------------------------------------------
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --------------------------------------------------------------------------
    # Security Context (nullable — not always available)
    #
    # ip_address: IPv4 (15 chars) or IPv6 (39 chars), max 45 chars.
    # user_agent: Browser/client identifier string (can be very long).
    #
    # Use case: "Your account was accessed from a new location" alert.
    # --------------------------------------------------------------------------
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --------------------------------------------------------------------------
    # Creation Timestamp
    #
    # No updated_at: Refresh tokens are immutable after creation.
    # Only is_revoked changes, which has its own semantic meaning.
    # --------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --------------------------------------------------------------------------
    # Relationship back to User
    # --------------------------------------------------------------------------
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_valid(self) -> bool:
        """Helper property: True if token is not revoked and not expired."""
        from datetime import timezone
        return (
            not self.is_revoked
            and self.expires_at.replace(tzinfo=timezone.utc) > __import__('datetime').datetime.now(timezone.utc)
        )

    def __repr__(self) -> str:
        return (
            f"<RefreshToken id={self.id!s:.8} "
            f"user_id={self.user_id!s:.8} "
            f"revoked={self.is_revoked}>"
        )
