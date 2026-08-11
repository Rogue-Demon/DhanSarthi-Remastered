"""Pydantic schemas for Transaction entity."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TransactionType


class TransactionResponse(BaseModel):
    """API response schema for Transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    transaction_type: TransactionType
    amount: Decimal
    category: Optional[str] = None
    description: Optional[str] = None
    transaction_date: date
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TransactionCreate(BaseModel):
    """Request schema for creating a Transaction record."""

    transaction_type: TransactionType
    amount: Decimal = Field(..., description="Transaction amount (must be positive)")
    category: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)
    transaction_date: date
    source: Optional[str] = Field(default=None, max_length=200)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v


class TransactionUpdate(BaseModel):
    """Request schema for updating a Transaction record."""

    transaction_type: Optional[TransactionType] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)
    transaction_date: Optional[date] = None
    source: Optional[str] = Field(default=None, max_length=200)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v
