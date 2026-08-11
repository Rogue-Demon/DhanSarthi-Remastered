"""Pydantic schemas for Loan and LoanPayment entities."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import LoanStatus, LoanType


class LoanPaymentResponse(BaseModel):
    """API response schema for LoanPayment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    loan_id: int
    amount: Decimal
    principal_component: Optional[Decimal] = None
    interest_component: Optional[Decimal] = None
    remaining_balance: Optional[Decimal] = None
    payment_date: date
    created_at: datetime


class LoanPaymentCreate(BaseModel):
    """Request schema for recording a LoanPayment."""

    amount: Decimal = Field(..., description="Payment amount")
    principal_component: Optional[Decimal] = Field(default=None)
    interest_component: Optional[Decimal] = Field(default=None)
    payment_date: date
    payment_method: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=255)

    @field_validator("amount")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v


class LoanResponse(BaseModel):
    """API response schema for Loan."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    loan_type: LoanType
    principal_amount: Decimal
    interest_rate_percent: Decimal
    tenure_months: int
    monthly_emi: Decimal
    start_date: date
    end_date: Optional[date] = None
    lender: Optional[str] = None
    status: LoanStatus
    collateral: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LoanCreate(BaseModel):
    """Request schema for creating a Loan record."""

    name: str = Field(..., min_length=1, max_length=100)
    loan_type: LoanType
    principal_amount: Decimal = Field(..., description="Principal amount (must be positive)")
    interest_rate_percent: Decimal = Field(..., description="Annual interest rate percentage")
    tenure_months: int = Field(..., description="Tenure in months (must be positive)")
    monthly_emi: Decimal = Field(..., description="Monthly EMI amount")
    start_date: date
    end_date: Optional[date] = Field(default=None)
    lender: Optional[str] = Field(default=None, max_length=100)
    status: LoanStatus = Field(default=LoanStatus.ACTIVE)
    collateral: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None, max_length=255)

    @field_validator("principal_amount", "monthly_emi")
    @classmethod
    def validate_positive_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Amount must be strictly positive")
        return v

    @field_validator("tenure_months")
    @classmethod
    def validate_positive_tenure(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Tenure months must be strictly positive")
        return v


class LoanUpdate(BaseModel):
    """Request schema for updating a Loan record."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    loan_type: Optional[LoanType] = None
    principal_amount: Optional[Decimal] = None
    interest_rate_percent: Optional[Decimal] = None
    tenure_months: Optional[int] = None
    monthly_emi: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    lender: Optional[str] = Field(default=None, max_length=100)
    status: Optional[LoanStatus] = None
    collateral: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None, max_length=255)
