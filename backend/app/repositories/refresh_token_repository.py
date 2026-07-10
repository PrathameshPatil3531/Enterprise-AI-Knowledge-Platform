"""
app/repositories/refresh_token_repository.py — Refresh Token Data Access Layer

All database operations for the RefreshToken model live here.

Key operations:
- create: Issue a new token record (called on login and on refresh)
- get_by_token_hash: Look up a token by its SHA-256 hash (called on every refresh)
- revoke: Mark a single token as revoked (single-device logout)
- revoke_all_for_user: Mark all tokens revoked (all-device logout, password change)
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Data access layer for the refresh_tokens table."""

    def create(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshToken:
        """
        Create and persist a new refresh token record.

        Args:
            user_id: The owner of this token.
            token_hash: SHA-256 hash of the raw token (never the raw token itself).
            expires_at: Absolute expiration timestamp (UTC).
            ip_address: Client IP for security audit (optional).
            user_agent: Client user-agent string for security audit (optional).

        Returns:
            The persisted RefreshToken ORM object.
        """
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    def get_by_token_hash(self, db: Session, *, token_hash: str) -> RefreshToken | None:
        """
        Look up a refresh token by its SHA-256 hash.

        This is called on every /auth/refresh request.
        The index on token_hash makes this a fast O(log n) lookup.

        Returns:
            The RefreshToken if found (may be revoked or expired — caller checks).
            None if no token with this hash exists.
        """
        return (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

    def revoke(self, db: Session, *, token_id: uuid.UUID) -> None:
        """
        Mark a single refresh token as revoked.

        Used for single-device logout.
        We update is_revoked=True rather than deleting the row, which allows
        us to detect token reuse (if someone presents a revoked token, it may be stolen).
        """
        token = db.get(RefreshToken, token_id)
        if token:
            token.is_revoked = True
            db.commit()

    def revoke_all_for_user(self, db: Session, *, user_id: uuid.UUID) -> int:
        """
        Revoke ALL active refresh tokens for a user.

        Used for:
        - All-device logout
        - Password change (force re-login on all devices for security)
        - Token reuse attack detected

        Returns:
            The number of tokens revoked.
        """
        result = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
            .update({"is_revoked": True}, synchronize_session="fetch")
        )
        db.commit()
        return result

    def delete_expired(self, db: Session) -> int:
        """
        Delete all expired refresh tokens from the database.

        Run this periodically (e.g., nightly via a cron job) to prevent
        the refresh_tokens table from growing unbounded.

        Returns:
            The number of tokens deleted.
        """
        from datetime import timezone
        now = datetime.now(timezone.utc)
        result = (
            db.query(RefreshToken)
            .filter(RefreshToken.expires_at < now)
            .delete(synchronize_session="fetch")
        )
        db.commit()
        return result


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------
refresh_token_repository = RefreshTokenRepository()
