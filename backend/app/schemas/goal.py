"""Pydantic schemas for Goal entity."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import GoalStatus


class GoalResponse(BaseModel):
    """API response schema for Goal."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    user_id: int
    title: str = Field(validation_alias="name")
    target_amount: Decimal
    current_amount: Decimal
    target_date: Optional[date] = None
    status: GoalStatus
    priority: int
    created_at: datetime
    updated_at: datetime


class GoalCreate(BaseModel):
    """Request schema for creating a Goal record."""

    title: str = Field(..., min_length=1, max_length=100)
    target_amount: Decimal = Field(..., description="Target monetary amount")
    current_amount: Decimal = Field(default=Decimal("0"), description="Currently saved amount")
    target_date: Optional[date] = None
    status: GoalStatus = Field(default=GoalStatus.ACTIVE)
    priority: int = Field(default=3, ge=1, le=5)

    @field_validator("target_amount")
    @classmethod
    def validate_positive_target(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Target amount must be strictly positive")
        return v

    @field_validator("current_amount")
    @classmethod
    def validate_non_negative_current(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Current amount cannot be negative")
        return v


class GoalUpdate(BaseModel):
    """Request schema for updating a Goal record."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    target_amount: Optional[Decimal] = None
    current_amount: Optional[Decimal] = None
    target_date: Optional[date] = None
    status: Optional[GoalStatus] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)

    @field_validator("target_amount")
    @classmethod
    def validate_positive_target(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Target amount must be strictly positive")
        return v

    @field_validator("current_amount")
    @classmethod
    def validate_non_negative_current(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < Decimal("0"):
            raise ValueError("Current amount cannot be negative")
        return v
