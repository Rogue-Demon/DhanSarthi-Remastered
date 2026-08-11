"""Pydantic schemas for authentication endpoints.

These schemas define the request/response contracts for:
    POST /api/v1/auth/register
    POST /api/v1/auth/login

The password field is write-only — it is never returned in any response.
The password_hash field is excluded from every response schema.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class UserRegisterRequest(BaseModel):
    """Registration request — email + password."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters)",
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Case-insensitive email normalization."""
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password must not be empty or whitespace-only.")
        return v


class LoginRequest(BaseModel):
    """Login request — email + password."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TokenResponse(BaseModel):
    """Standard OAuth2 token response."""

    access_token: str
    token_type: str = "bearer"


class AuthenticatedUserResponse(BaseModel):
    """Safe user information — never exposes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
