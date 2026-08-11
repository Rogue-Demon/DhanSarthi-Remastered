"""Pydantic schemas for Liability entity."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import LiabilityType


class LiabilityResponse(BaseModel):
    """API response schema for Liability."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    user_id: int
    name: str
    liability_type: LiabilityType
    outstanding_balance: Decimal = Field(validation_alias="outstanding_amount")
    interest_rate_percent: Optional[Decimal] = Field(
        default=None, validation_alias="interest_rate"
    )
    created_at: datetime
    updated_at: datetime


class LiabilityCreate(BaseModel):
    """Request schema for creating a Liability record."""

    name: str = Field(..., min_length=1, max_length=100)
    liability_type: LiabilityType
    outstanding_balance: Decimal = Field(..., description="Outstanding balance amount")
    interest_rate_percent: Optional[Decimal] = Field(default=None)

    @field_validator("outstanding_balance")
    @classmethod
    def validate_non_negative_amount(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Amount cannot be negative")
        return v


class LiabilityUpdate(BaseModel):
    """Request schema for updating a Liability record."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    liability_type: Optional[LiabilityType] = None
    outstanding_balance: Optional[Decimal] = None
    interest_rate_percent: Optional[Decimal] = None

    @field_validator("outstanding_balance")
    @classmethod
    def validate_non_negative_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < Decimal("0"):
            raise ValueError("Amount cannot be negative")
        return v
