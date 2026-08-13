"""Pydantic schemas for Profile entity."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Persona, RiskProfile


class ProfileResponse(BaseModel):
    """API response schema for user profile."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    persona: Persona
    display_name: Optional[str] = None
    country: str
    currency: str
    risk_profile: Optional[RiskProfile] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    occupation: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = None
    occupation: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProfileCreate(BaseModel):
    """Schema for profile creation."""

    persona: Persona = Field(default=Persona.PROFESSIONAL)
    display_name: Optional[str] = Field(default=None, max_length=100)
    country: str = Field(default="IN", max_length=10)
    currency: str = Field(default="INR", max_length=10)
    risk_profile: Optional[RiskProfile] = Field(default=RiskProfile.MODERATE)


class ProfileUpdate(BaseModel):
    """Schema for profile partial update."""

    persona: Optional[Persona] = None
    display_name: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=10)
    currency: Optional[str] = Field(default=None, max_length=10)
    risk_profile: Optional[RiskProfile] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    occupation: Optional[str] = Field(default=None, max_length=100)
