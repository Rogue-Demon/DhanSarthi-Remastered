"""Pydantic schemas for Investment and InvestmentTransaction entities."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import InvestmentTransactionType, InvestmentType


class InvestmentTransactionResponse(BaseModel):
    """API response schema for InvestmentTransaction."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    investment_id: int
    transaction_type: InvestmentTransactionType
    amount: Decimal
    units: Optional[Decimal] = Field(default=None, validation_alias="quantity")
    price_per_unit: Optional[Decimal] = None
    transaction_date: date
    notes: Optional[str] = None
    created_at: datetime


class InvestmentTransactionCreate(BaseModel):
    """Request schema for recording an InvestmentTransaction."""

    transaction_type: InvestmentTransactionType
    amount: Decimal = Field(..., description="Transaction monetary amount")
    units: Optional[Decimal] = Field(default=None)
    price_per_unit: Optional[Decimal] = Field(default=None)
    transaction_date: date
    notes: Optional[str] = Field(default=None, max_length=255)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v


class InvestmentResponse(BaseModel):
    """API response schema for Investment."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    user_id: int
    name: str
    investment_type: InvestmentType
    invested_amount: Decimal = Field(validation_alias="principal")
    current_value: Decimal
    units: Optional[Decimal] = Field(default=None, validation_alias="quantity")
    purchase_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class InvestmentCreate(BaseModel):
    """Request schema for creating an Investment record."""

    name: str = Field(..., min_length=1, max_length=100)
    investment_type: InvestmentType
    invested_amount: Decimal = Field(..., description="Total invested amount")
    current_value: Decimal = Field(..., description="Current holding value")
    units: Optional[Decimal] = Field(default=None)
    purchase_date: Optional[date] = Field(default=None)
    ticker_symbol: Optional[str] = Field(default=None, max_length=20)
    institution: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=255)

    @field_validator("invested_amount", "current_value")
    @classmethod
    def validate_non_negative_amount(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Amount cannot be negative")
        return v


class InvestmentUpdate(BaseModel):
    """Request schema for updating an Investment record."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    investment_type: Optional[InvestmentType] = None
    invested_amount: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    units: Optional[Decimal] = None
    purchase_date: Optional[date] = None
    ticker_symbol: Optional[str] = Field(default=None, max_length=20)
    institution: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=255)

    @field_validator("invested_amount", "current_value")
    @classmethod
    def validate_non_negative_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < Decimal("0"):
            raise ValueError("Amount cannot be negative")
        return v
