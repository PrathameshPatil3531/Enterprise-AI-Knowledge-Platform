"""
app/core/security.py — Cryptographic Utilities

This module is the ONLY place in the codebase that performs:
- Password hashing (bcrypt via passlib)
- JWT token creation and validation (via python-jose)
- Refresh token generation (cryptographic random) and hashing (SHA-256)

WHY isolate this?
- Single responsibility: one file owns all crypto logic
- Reusable by services, routes, and tests without circular imports
- Easy to swap algorithms (e.g., bcrypt → argon2) in one place

IMPORTANT: This file must NOT import anything from app.services, app.api,
or app.repositories. It only imports from app.core.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

# ---------------------------------------------------------------------------
# Password Hashing
#
# CryptContext manages multiple hashing schemes and handles scheme migration.
#
# schemes=["bcrypt"]:
#   Use bcrypt as the hashing algorithm.
#   bcrypt is intentionally slow (configurable cost factor, default=12 rounds).
#   It takes ~100ms per hash — negligible for users, prohibitive for attackers.
#
# deprecated="auto":
#   If a user has a hash from an older/weaker scheme, passlib will flag it
#   so the application can re-hash it with bcrypt on their next login.
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    bcrypt automatically:
    - Generates a unique salt (random bytes mixed into the hash)
    - Embeds the salt in the returned hash string
    - Applies 12 rounds of key stretching by default

    This means two calls with the same password produce DIFFERENT hashes.
    This is correct and expected behavior.

    Example output:
        "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Uses constant-time comparison internally to prevent timing attacks.
    Returns True if they match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT Access Token
# ---------------------------------------------------------------------------

def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """
    Create a signed JWT access token.

    Payload claims:
        sub  — Subject: the user's UUID (who this token represents)
        exp  — Expiration: when the token becomes invalid (15 minutes)
        iat  — Issued At: when the token was created
        type — Custom claim: "access" (distinguishes from refresh tokens)

    The token is signed with SECRET_KEY using HS256 (HMAC-SHA256).
    Anyone with SECRET_KEY can verify the signature — no DB lookup needed.

    Args:
        subject: The user's UUID as a string.
        extra_claims: Optional additional claims (e.g., org_id, role — added in Milestone 3).

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": subject,    # User UUID
        "exp": expire,     # Expiration (python-jose validates this automatically)
        "iat": now,        # Issued at
        "type": "access",  # Token type guard — prevents refresh tokens being used as access
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Validates:
    - Signature (was this signed by our SECRET_KEY?)
    - Expiration (is it still within the TTL?)
    - Token type (is it an "access" token, not a refresh token?)

    Raises:
        UnauthorizedException: If token is invalid, expired, or wrong type.

    Returns:
        Decoded payload dictionary containing sub, exp, iat, type.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        # JWTError covers: ExpiredSignatureError, JWTClaimsError, DecodeError
        raise UnauthorizedException("Token is invalid or has expired")

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    return payload


# ---------------------------------------------------------------------------
# Refresh Token
#
# Refresh tokens are NOT JWTs. They are:
# - Opaque random bytes (128 hex characters = 64 bytes of entropy)
# - Stored as SHA-256 hashes in the database
# - Delivered to clients via HTTP-only cookies
#
# WHY not JWT for refresh tokens?
# - Refresh tokens must be revocable (stored in DB) — so stateless JWT
#   offers no advantage for them.
# - Random opaque tokens are simpler and just as secure for this purpose.
# ---------------------------------------------------------------------------

def create_refresh_token() -> tuple[str, str]:
    """
    Generate a cryptographically secure refresh token.

    Returns:
        (raw_token, hashed_token) tuple where:
        - raw_token   → Sent to the client inside an HTTP-only cookie
        - hashed_token → Stored in the database (SHA-256 of raw_token)

    Why store the hash, not the raw token?
        If the database is compromised, an attacker finds only SHA-256 hashes.
        They cannot reverse SHA-256 to get the raw token.
        The raw token itself has 64 bytes of entropy — brute-forcing is infeasible.
    """
    raw_token = secrets.token_hex(64)  # 128 hex chars = 64 bytes = 512 bits of entropy
    hashed_token = hash_refresh_token(raw_token)
    return raw_token, hashed_token


def hash_refresh_token(raw_token: str) -> str:
    """
    Hash a raw refresh token using SHA-256 for safe database storage.

    SHA-256 is appropriate here (unlike passwords) because:
    - The raw token already has 64 bytes of randomness (not a guessable word)
    - SHA-256 is deterministic — same input always produces the same hash
      which is needed to look up the token in the database
    - Salt is unnecessary because random tokens are unique by design

    Args:
        raw_token: The raw hex string from create_refresh_token().

    Returns:
        64-character lowercase hex string (SHA-256 hash).
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def dummy_verify() -> None:
    """
    Run a bcrypt verification that always fails.

    PURPOSE: Timing attack prevention.

    Problem:
        If we check "does email exist?" BEFORE running bcrypt, then:
        - Email not found → response in 1ms (no bcrypt)
        - Email found, wrong password → response in 100ms (bcrypt ran)
        An attacker can determine which emails are registered by measuring response time.

    Solution:
        Always run bcrypt, even when the user doesn't exist.
        Use this function to run a dummy verification against an invalid hash.
        Now both "email not found" and "wrong password" take ~100ms.
    """
    pwd_context.dummy_verify()
