"""
app/services/auth_service.py — Authentication Business Logic

This service orchestrates ALL authentication use cases.
It calls repositories for data access and security utilities for cryptography.

RULES enforced here:
- Never write SQL queries (that's the repository's job)
- Never reference HTTP concepts like Request, Response, cookies, status codes
- Never import from app.api (that creates a circular dependency)

WHY a service layer?
- Routes become thin: just validate input → call service → return output
- Business logic is testable without an HTTP layer or real database
- A single use case (e.g., "login") can be called from REST, GraphQL, or CLI
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    dummy_verify,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import refresh_token_repository
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    """
    Orchestrates all authentication and user identity use cases.

    Public methods (each = one use case):
        register        → Create a new user account
        login           → Authenticate and issue tokens
        refresh         → Exchange a refresh token for new tokens (with rotation)
        logout          → Revoke a single refresh token
        logout_all      → Revoke all refresh tokens for a user
        change_password → Change password and invalidate all sessions
        get_user        → Fetch authenticated user's profile
    """

    # ------------------------------------------------------------------
    # REGISTER
    # ------------------------------------------------------------------
    def register(self, db: Session, *, user_data: UserCreate) -> User:
        """
        Register a new user account.

        Steps:
        1. Check if email already exists → raise ConflictException if yes
        2. Hash the password with bcrypt
        3. Create the user record
        4. Return the created User ORM object

        Raises:
            ConflictException: If the email is already registered.
        """
        # Check for duplicate email before attempting to insert.
        # This gives a clean 409 Conflict error rather than a DB IntegrityError.
        if user_repository.email_exists(db, email=user_data.email):
            raise ConflictException("Email address")

        password_hash = hash_password(user_data.password)

        user = user_repository.create(
            db,
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name,
        )

        logger.info("New user registered | email=%s | id=%s", user.email, user.id)
        return user

    # ------------------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------------------
    def login(
        self,
        db: Session,
        *,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str, str]:
        """
        Authenticate a user with email and password.

        Returns:
            (user, access_token, raw_refresh_token)
            The raw_refresh_token must be sent to the client as an HTTP-only cookie.

        Raises:
            UnauthorizedException: If credentials are invalid or account is deactivated.

        Security note — Timing Attack Prevention:
            We ALWAYS run bcrypt verification, even if the user email doesn't exist.
            Without this, an attacker can determine registered emails by measuring
            response time (no user = no bcrypt = ~1ms vs ~100ms with bcrypt).
            `dummy_verify()` runs a full bcrypt round against a dummy hash,
            making both paths take the same amount of time.
        """
        user = user_repository.get_by_email(db, email=email)

        if not user:
            dummy_verify()  # Timing attack prevention — MUST be called before raising
            raise UnauthorizedException("Incorrect email or password")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Incorrect email or password")

        if not user.is_active:
            # Separate message for deactivated accounts (not a security risk to reveal this)
            raise UnauthorizedException("This account has been deactivated. Please contact support.")

        # --- Create JWT access token (stateless, 15 min TTL) ---
        access_token = create_access_token(subject=str(user.id))

        # --- Create opaque refresh token (stateful, 7 day TTL) ---
        raw_refresh_token, token_hash = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        refresh_token_repository.create(
            db,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # --- Update last login timestamp ---
        user_repository.update_last_login(db, user_id=user.id)

        logger.info(
            "User logged in | email=%s | id=%s | ip=%s",
            user.email, user.id, ip_address,
        )
        return user, access_token, raw_refresh_token

    # ------------------------------------------------------------------
    # REFRESH (Token Rotation)
    # ------------------------------------------------------------------
    def refresh(
        self,
        db: Session,
        *,
        raw_refresh_token: str,
    ) -> tuple[str, str]:
        """
        Exchange a valid refresh token for a new access token + new refresh token.

        Implements Token Rotation:
            - Old refresh token is immediately revoked
            - New refresh token is issued
            - This means a stolen token can only be used ONCE before becoming invalid

        Implements Reuse Detection:
            - If a REVOKED token is presented, it may have been stolen
            - We immediately revoke ALL tokens for this user (most defensive response)
            - This forces re-authentication on all devices

        Returns:
            (new_access_token, new_raw_refresh_token)

        Raises:
            UnauthorizedException: Token invalid, revoked, expired, or user inactive.
        """
        token_hash = hash_refresh_token(raw_refresh_token)
        stored_token = refresh_token_repository.get_by_token_hash(db, token_hash=token_hash)

        if not stored_token:
            raise UnauthorizedException("Refresh token is invalid")

        # --- Reuse Detection ---
        if stored_token.is_revoked:
            logger.warning(
                "SECURITY: Revoked refresh token presented — possible token theft. "
                "Revoking all tokens for user_id=%s",
                stored_token.user_id,
            )
            # Revoke ALL tokens — even new ones that may have been issued to the attacker
            refresh_token_repository.revoke_all_for_user(db, user_id=stored_token.user_id)
            raise UnauthorizedException(
                "Refresh token has already been used or revoked. "
                "Please log in again."
            )

        # --- Expiry Check ---
        now = datetime.now(timezone.utc)
        token_expiry = stored_token.expires_at
        # Ensure timezone-aware comparison (PostgreSQL returns timezone-aware datetimes)
        if token_expiry.tzinfo is None:
            token_expiry = token_expiry.replace(tzinfo=timezone.utc)

        if token_expiry < now:
            raise UnauthorizedException("Refresh token has expired. Please log in again.")

        # --- User Validation ---
        user = user_repository.get_by_id(db, user_id=stored_token.user_id)
        if not user:
            raise UnauthorizedException("User account not found or deactivated")

        # --- Token Rotation ---
        # Revoke the used token immediately
        refresh_token_repository.revoke(db, token_id=stored_token.id)

        # Issue a brand new pair of tokens
        new_access_token = create_access_token(subject=str(user.id))
        new_raw_refresh_token, new_token_hash = create_refresh_token()
        new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token_repository.create(
            db,
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            # Carry forward security context from original token
            ip_address=stored_token.ip_address,
            user_agent=stored_token.user_agent,
        )

        logger.info("Token refreshed | user_id=%s", user.id)
        return new_access_token, new_raw_refresh_token

    # ------------------------------------------------------------------
    # LOGOUT (Single Device)
    # ------------------------------------------------------------------
    def logout(self, db: Session, *, raw_refresh_token: str) -> None:
        """
        Revoke the current refresh token (log out of this device only).

        The access token will expire naturally after its TTL (15 minutes).
        This is an accepted trade-off for stateless JWTs.
        In high-security scenarios, a token denylist (Redis) can be used.
        """
        token_hash = hash_refresh_token(raw_refresh_token)
        stored_token = refresh_token_repository.get_by_token_hash(
            db, token_hash=token_hash
        )

        if stored_token and not stored_token.is_revoked:
            refresh_token_repository.revoke(db, token_id=stored_token.id)
            logger.info("User logged out | token_id=%s", stored_token.id)

    # ------------------------------------------------------------------
    # LOGOUT ALL DEVICES
    # ------------------------------------------------------------------
    def logout_all(self, db: Session, *, user_id: uuid.UUID) -> int:
        """
        Revoke ALL active refresh tokens for a user.

        Use when:
        - User selects "Log out of all devices" in settings
        - Admin deactivates an account
        - Security breach detected

        Returns:
            Number of tokens revoked.
        """
        count = refresh_token_repository.revoke_all_for_user(db, user_id=user_id)
        logger.info("All sessions revoked | user_id=%s | count=%d", user_id, count)
        return count

    # ------------------------------------------------------------------
    # CHANGE PASSWORD
    # ------------------------------------------------------------------
    def change_password(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change a user's password.

        Security requirements:
        1. Current password must be verified (prevents unauthorized changes)
        2. New password must be different from current
        3. After success, ALL refresh tokens are revoked (force re-login everywhere)
           Rationale: If an attacker got access and changed the password,
                      revoking all tokens kicks them out too.

        Raises:
            NotFoundException: If user not found.
            UnauthorizedException: If current password is wrong.
            BadRequestException: If new password equals current password.
        """
        user = user_repository.get_by_id(db, user_id=user_id)
        if not user:
            raise NotFoundException("User")

        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedException("Current password is incorrect")

        if verify_password(new_password, user.password_hash):
            raise BadRequestException(
                "New password must be different from the current password"
            )

        new_hash = hash_password(new_password)
        user_repository.update_password(db, user_id=user_id, new_hash=new_hash)

        # Revoke all active sessions — this is a deliberate security decision
        revoked_count = refresh_token_repository.revoke_all_for_user(
            db, user_id=user_id
        )

        logger.info(
            "Password changed | user_id=%s | sessions_revoked=%d",
            user_id, revoked_count,
        )

    # ------------------------------------------------------------------
    # GET USER PROFILE
    # ------------------------------------------------------------------
    def get_user(self, db: Session, *, user_id: uuid.UUID) -> User:
        """
        Fetch a user's profile by ID.

        Raises:
            NotFoundException: If user does not exist or is deactivated.
        """
        user = user_repository.get_by_id(db, user_id=user_id)
        if not user:
            raise NotFoundException("User")
        return user


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------
auth_service = AuthService()
