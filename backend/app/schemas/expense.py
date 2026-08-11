"""Pydantic schemas for Expense entity."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ExpenseFrequency


class ExpenseResponse(BaseModel):
    """API response schema for Expense."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category: str
    amount: Decimal
    expense_date: date
    currency: str
    frequency: Optional[ExpenseFrequency] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExpenseCreate(BaseModel):
    """Request schema for creating an Expense record."""

    category: str = Field(default="Other", max_length=50)
    amount: Decimal = Field(..., description="Expense amount (must be positive)")
    expense_date: date
    currency: str = Field(default="INR", max_length=10)
    frequency: Optional[ExpenseFrequency] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=255)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v


class ExpenseUpdate(BaseModel):
    """Request schema for updating an Expense record."""

    category: Optional[str] = Field(default=None, max_length=50)
    amount: Optional[Decimal] = None
    expense_date: Optional[date] = None
    currency: Optional[str] = Field(default=None, max_length=10)
    frequency: Optional[ExpenseFrequency] = None
    description: Optional[str] = Field(default=None, max_length=255)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v
