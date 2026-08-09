"""Minimal Pydantic schemas for User — for testing and future API use.

Full CRUD request/response schemas for every entity will be built in the
API implementation phases.  Only the foundational read schema is provided
here to validate model-to-schema mapping works correctly.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserRead(BaseModel):
    """Read schema for a User record.

    Used to validate that SQLAlchemy User instances serialize correctly
    to Pydantic.  ``from_attributes=True`` enables ORM mode.
    """

    id: int
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Minimal creation schema — used in tests only.

    Authentication fields will be added in the Authentication phase.
    """

    email: str

    @field_validator("email")
    @classmethod
    def email_must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("email must not be empty")
        return v.lower().strip()
