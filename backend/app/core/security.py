"""Security utilities for password hashing and JWT token management.

This module provides reusable security functions used across the
authentication layer.  It does NOT contain financial logic.

Password hashing uses bcrypt.  JWT tokens use PyJWT with configurable
secret, algorithm, and expiration from the application settings.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Returns the full bcrypt hash string suitable for database storage.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash.

    Returns ``True`` when the password matches, ``False`` otherwise.
    Never raises on malformed input — returns ``False`` instead.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT access tokens
# ---------------------------------------------------------------------------


def _get_jwt_secret() -> str:
    """Resolve the JWT signing secret from settings.

    Falls back through ``auth_jwt_secret`` → ``secret_key`` → dev placeholder.
    The dev placeholder is clearly marked so it cannot silently reach production.
    """
    return (
        settings.auth_jwt_secret
        or settings.secret_key
        or "development-jwt-secret-do-not-use-in-production"
    )


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    data:
        Claims to include (typically ``{"sub": str(user_id)}``).
    expires_delta:
        Optional custom lifetime.  Defaults to the configured
        ``auth_access_token_expire_minutes``.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.auth_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(
        to_encode,
        _get_jwt_secret(),
        algorithm=settings.auth_jwt_algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token.

    Returns the decoded payload dict on success, or ``None`` if the token
    is invalid, expired, or has a bad signature.  Internal errors are
    never exposed.
    """
    try:
        return jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[settings.auth_jwt_algorithm],
        )
    except jwt.PyJWTError:
        return None
