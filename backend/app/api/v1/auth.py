"""Authentication API router for DhanSarthi.

Public endpoints:
    POST /api/v1/auth/register — Create a new user account.
    POST /api/v1/auth/login    — Authenticate and receive an access token.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    AuthenticatedUserResponse,
    LoginRequest,
    TokenResponse,
    UserRegisterRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=AuthenticatedUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    data: UserRegisterRequest,
    service: AuthService = Depends(_get_auth_service),
) -> AuthenticatedUserResponse:
    """Create a new user account.

    Steps performed server-side:
        1. Validate and normalize email.
        2. Check for duplicate accounts.
        3. Hash the password with bcrypt.
        4. Persist the new user.
        5. Auto-provision a default profile.
        6. Return safe user information (never the password hash).
    """
    user = service.register(email=data.email, password=data.password)
    return AuthenticatedUserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive an access token",
)
def login(
    data: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """Authenticate with email and password.

    Returns a standard ``{access_token, token_type}`` response on success.

    Error responses use a generic message to prevent user enumeration.
    """
    user = service.authenticate(email=data.email, password=data.password)
    token_data = service.create_token_for_user(user)
    return TokenResponse(**token_data)
