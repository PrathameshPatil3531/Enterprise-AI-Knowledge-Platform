"""
app/repositories/user_repository.py — User Data Access Layer

All database operations for the User model live here.
Services call this repository — they never write SQLAlchemy queries directly.

WHY this pattern?
- Single location for all User-related DB logic
- If the query needs to change (add filter, change join), change it here only
- Service layer remains unchanged and unaware of how data is fetched
- Testing: mock this repository → test service without a real database

Design note: The repository instance is a singleton (one shared object).
It is stateless — db is always passed as a parameter, never stored.
This makes it thread-safe in concurrent request scenarios.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Data access layer for the users table."""

    def get_by_id(self, db: Session, *, user_id: uuid.UUID) -> User | None:
        """
        Fetch an active user by their UUID primary key.

        Returns None if the user does not exist OR if is_active=False.
        We filter on is_active here so services don't need to check separately.
        """
        return (
            db.query(User)
            .filter(User.id == user_id, User.is_active == True)  # noqa: E712
            .first()
        )

    def get_by_id_including_inactive(self, db: Session, *, user_id: uuid.UUID) -> User | None:
        """
        Fetch a user by UUID regardless of active status.
        Used for admin operations (e.g., reactivating a user).
        """
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, *, email: str) -> User | None:
        """
        Fetch a user by email address.

        Email is normalized to lowercase before querying.
        Returns the user whether active or not (needed during login to give
        a "deactivated" message rather than "incorrect credentials").
        """
        return db.query(User).filter(User.email == email.lower()).first()

    def email_exists(self, db: Session, *, email: str) -> bool:
        """
        Check if an email is already registered.
        More efficient than get_by_email when you only need a boolean.
        """
        return (
            db.query(User.id)
            .filter(User.email == email.lower())
            .first()
        ) is not None

    def create(
        self,
        db: Session,
        *,
        email: str,
        password_hash: str,
        full_name: str | None = None,
    ) -> User:
        """
        Create a new user record and return the persisted object.

        Email is normalized to lowercase.
        db.refresh(user) reloads the row from the DB so server_default values
        (like created_at) are available on the returned object.
        """
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)  # Reload from DB to get server_default values (created_at, etc.)
        return user

    def update_last_login(self, db: Session, *, user_id: uuid.UUID) -> None:
        """
        Set last_login to the current UTC timestamp.
        Called on every successful login.
        """
        user = db.get(User, user_id)
        if user:
            user.last_login = datetime.now(timezone.utc)
            db.commit()

    def update_password(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        new_hash: str,
    ) -> None:
        """
        Update the stored password hash.
        Called after the service has validated the current password and hashed the new one.
        """
        user = db.get(User, user_id)
        if user:
            user.password_hash = new_hash
            db.commit()

    def deactivate(self, db: Session, *, user_id: uuid.UUID) -> None:
        """
        Soft-delete a user by setting is_active=False.
        The user row and all related data are preserved.
        """
        user = db.get(User, user_id)
        if user:
            user.is_active = False
            db.commit()

    def set_verified(self, db: Session, *, user_id: uuid.UUID) -> None:
        """
        Mark a user's email as verified.
        Called when the user clicks the verification link (future milestone).
        """
        user = db.get(User, user_id)
        if user:
            user.is_verified = True
            db.commit()


# ---------------------------------------------------------------------------
# Singleton instance
#
# Import and use this everywhere:
#   from app.repositories.user_repository import user_repository
#   user = user_repository.get_by_email(db, email=email)
# ---------------------------------------------------------------------------
user_repository = UserRepository()
