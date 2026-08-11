"""Pydantic schemas for Asset entity."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import AssetType


class AssetResponse(BaseModel):
    """API response schema for Asset."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    user_id: int
    name: str
    asset_type: AssetType
    current_value: Decimal = Field(validation_alias="value")
    valuation_date: date
    created_at: datetime
    updated_at: datetime


class AssetCreate(BaseModel):
    """Request schema for creating an Asset record."""

    name: str = Field(..., min_length=1, max_length=100)
    asset_type: AssetType
    current_value: Decimal = Field(..., description="Asset current monetary value")
    valuation_date: Optional[date] = Field(default=None)

    @field_validator("current_value")
    @classmethod
    def validate_non_negative_value(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Current value cannot be negative")
        return v


class AssetUpdate(BaseModel):
    """Request schema for updating an Asset record."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    asset_type: Optional[AssetType] = None
    current_value: Optional[Decimal] = None
    valuation_date: Optional[date] = None

    @field_validator("current_value")
    @classmethod
    def validate_non_negative_value(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < Decimal("0"):
            raise ValueError("Current value cannot be negative")
        return v
