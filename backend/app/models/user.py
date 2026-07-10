"""
app/models/user.py — User ORM Model

Maps the `users` table in PostgreSQL.

Design decisions:
- No `role` column: Roles are per-organization, stored in `memberships` (Milestone 3).
- No `org_id`: A user can belong to multiple organizations (memberships table).
- `is_active` as soft-delete: Deactivating a user preserves audit history.
- `is_verified`: Email verification flag (enforcement added in future milestone).
- `last_login`: Security audit — detect inactive or suspicious accounts.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """
    Represents a registered user of the platform.

    A user has an account-level identity. Their organization membership
    and roles are managed separately via the Membership model (Milestone 3).
    """

    __tablename__ = "users"

    # --------------------------------------------------------------------------
    # Primary Key
    #
    # UUID v4 (random). Generated in Python before the DB insert so the ID is
    # available immediately (for logging, related record creation, etc.).
    #
    # UUID vs Auto-increment integer:
    # - UUIDs are globally unique → safe to merge data from multiple DBs
    # - UUIDs cannot be enumerated → GET /users/1, /users/2 attack is impossible
    # - Slight performance cost (16 bytes vs 4 bytes index) — acceptable for our scale
    # --------------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # --------------------------------------------------------------------------
    # Email
    #
    # The user's login credential and unique identifier.
    # - unique=True: Enforced at both DB and application level
    # - index=True: B-tree index for fast lookup by email (O(log n) vs O(n))
    # - Always stored lowercase (normalized in the repository layer)
    # --------------------------------------------------------------------------
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------------------------
    # Password Hash
    #
    # Stores the bcrypt hash of the user's password.
    # NEVER store the plain-text password.
    # bcrypt hash is always 60 characters, but we use 255 for future-proofing.
    # --------------------------------------------------------------------------
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # --------------------------------------------------------------------------
    # Full Name — Optional display name shown in the UI
    # --------------------------------------------------------------------------
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --------------------------------------------------------------------------
    # is_active — Soft-delete flag
    #
    # When is_active=False:
    # - User cannot log in
    # - User does not appear in member lists
    # - User's data (documents, messages) is preserved for audit purposes
    #
    # Why soft-delete instead of deleting the row?
    # - Preserves audit trails (who uploaded what, who sent what message)
    # - Safe to restore an account if deactivated by mistake
    # - Foreign key references to the user remain valid
    # --------------------------------------------------------------------------
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --------------------------------------------------------------------------
    # is_verified — Email verification flag
    #
    # Currently always False (verification not implemented yet).
    # In a future milestone, we will:
    # 1. Send a verification email on registration
    # 2. Set is_verified=True when the user clicks the link
    # 3. Optionally block login until verified
    # --------------------------------------------------------------------------
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --------------------------------------------------------------------------
    # last_login — Security audit timestamp
    #
    # Updated on every successful login.
    # Use cases:
    # - Admin dashboard: show last seen date
    # - Detect dormant accounts (inactive for 90+ days)
    # - Security alert: login from unusual location
    # --------------------------------------------------------------------------
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --------------------------------------------------------------------------
    # Timestamps
    #
    # server_default=func.now():
    #   PostgreSQL sets this to the current timestamp at INSERT time.
    #   "server" means the DB sets it, not Python — avoids clock skew.
    #
    # onupdate=func.now():
    #   SQLAlchemy updates this field automatically on every ORM-level UPDATE.
    # --------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --------------------------------------------------------------------------
    # Relationships
    #
    # cascade="all, delete-orphan":
    #   When a User is deleted via ORM, all their RefreshTokens are auto-deleted.
    #   "orphan" handling: if a RefreshToken is removed from user.refresh_tokens list,
    #   it gets deleted from the DB automatically.
    # --------------------------------------------------------------------------
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",  # Load refresh_tokens only when accessed explicitly
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!s:.8} email={self.email} active={self.is_active}>"
