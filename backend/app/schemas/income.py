"""Pydantic schemas for Income entity."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import IncomeFrequency


class IncomeResponse(BaseModel):
    """API response schema for Income."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    source: str
    amount: Decimal
    income_date: date
    category: str
    currency: str
    frequency: IncomeFrequency
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncomeCreate(BaseModel):
    """Request schema for creating an Income record."""

    source: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., description="Income amount (must be positive)")
    income_date: date
    category: str = Field(default="Other", max_length=50)
    currency: str = Field(default="INR", max_length=10)
    frequency: IncomeFrequency = Field(default=IncomeFrequency.ONE_TIME)
    description: Optional[str] = Field(default=None, max_length=255)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v


class IncomeUpdate(BaseModel):
    """Request schema for updating an Income record."""

    source: Optional[str] = Field(default=None, min_length=1, max_length=100)
    amount: Optional[Decimal] = None
    income_date: Optional[date] = None
    category: Optional[str] = Field(default=None, max_length=50)
    currency: Optional[str] = Field(default=None, max_length=10)
    frequency: Optional[IncomeFrequency] = None
    description: Optional[str] = Field(default=None, max_length=255)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v
