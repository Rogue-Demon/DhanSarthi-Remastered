"""Authentication service for DhanSarthi.

Responsibilities:
    - User registration (with duplicate detection and password hashing).
    - Credential verification (email + password).
    - Access token generation.
    - Authenticated user resolution.

This service does NOT contain financial logic.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import (
    DhanSarthiError,
    ResourceAlreadyExistsError,
    handle_db_exceptions,
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth-specific exceptions
# ---------------------------------------------------------------------------


class AuthenticationError(DhanSarthiError):
    """Raised when authentication fails.

    Maps to HTTP 401 Unauthorized.
    Uses a generic message to avoid user enumeration.
    """

    def __init__(self, message: str = "Invalid credentials.") -> None:
        super().__init__(message)


class InactiveUserError(DhanSarthiError):
    """Raised when an inactive user attempts to authenticate.

    Maps to HTTP 403 Forbidden.
    """

    def __init__(self) -> None:
        super().__init__("User account is inactive.")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AuthService:
    """Coordinates user authentication workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._user_repo = UserRepository(db)
        self._profile_service = ProfileService(db)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, email: str, password: str) -> User:
        """Register a new user account.

        Steps:
            1. Normalize email.
            2. Check for existing account.
            3. Hash password.
            4. Create user.
            5. Create default profile.
            6. Return user.

        Raises ``ResourceAlreadyExistsError`` if email is already taken.
        """
        normalized_email = email.lower().strip()

        existing = self._user_repo.get_by_email(normalized_email)
        if existing is not None:
            raise ResourceAlreadyExistsError(resource="User")

        password_hash = hash_password(password)
        user = User(
            email=normalized_email,
            password_hash=password_hash,
        )

        with handle_db_exceptions(resource="User"):
            self._user_repo.add(user)
            self._db.commit()

        self._db.refresh(user)

        # Auto-provision default profile for onboarding.
        # Use the email's local part (before @) as the initial display name.
        display_name = normalized_email.split("@")[0]
        self._profile_service.get_or_create_profile(user.id, display_name=display_name)

        logger.info("User registered: id=%s", user.id)
        return user

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self, email: str, password: str) -> User:
        """Verify user credentials.

        Returns the authenticated ``User`` on success.

        Raises ``AuthenticationError`` (generic) for:
            - Unknown email.
            - Wrong password.
        Raises ``InactiveUserError`` when the account is deactivated.
        """
        normalized_email = email.lower().strip()
        user = self._user_repo.get_by_email(normalized_email)

        if user is None:
            raise AuthenticationError()

        if not verify_password(password, user.password_hash):
            raise AuthenticationError()

        if not user.is_active:
            raise InactiveUserError()

        return user

    # ------------------------------------------------------------------
    # Token generation
    # ------------------------------------------------------------------

    @staticmethod
    def create_token_for_user(user: User) -> dict:
        """Generate a JWT access token for *user*.

        The token payload contains only:
            - ``sub``: str(user.id)
            - ``exp``: expiration timestamp
            - ``iat``: issued-at timestamp

        Financial data is NEVER placed inside the token.
        """
        access_token = create_access_token(data={"sub": str(user.id)})
        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
