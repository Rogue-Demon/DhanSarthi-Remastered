"""Pydantic schemas for Budget entity."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import BudgetPeriod


class BudgetResponse(BaseModel):
    """API response schema for Budget."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category: str
    amount: Decimal
    period: BudgetPeriod
    start_date: date
    end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class BudgetCreate(BaseModel):
    """Request schema for creating a Budget record."""

    category: str = Field(..., min_length=1, max_length=50)
    amount: Decimal = Field(..., description="Budget monetary allocation limit")
    period: BudgetPeriod = Field(default=BudgetPeriod.MONTHLY)
    start_date: date
    end_date: Optional[date] = Field(default=None)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Budget amount must be strictly positive")
        return v


class BudgetUpdate(BaseModel):
    """Request schema for updating a Budget record."""

    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    amount: Optional[Decimal] = None
    period: Optional[BudgetPeriod] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Budget amount must be strictly positive")
        return v
