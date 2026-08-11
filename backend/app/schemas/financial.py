"""Pydantic schemas for Financial Engine calculation endpoints and API summaries."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LoanCalculateRequest(BaseModel):
    """Request payload for pure loan EMI calculation endpoint."""

    principal: Decimal = Field(..., description="Loan principal amount")
    annual_interest_rate_percent: Decimal = Field(..., description="Annual interest rate percentage")
    tenure_months: int = Field(..., description="Tenure in months")
    payment_frequency: str = Field(default="MONTHLY")

    @field_validator("principal")
    @classmethod
    def validate_positive_principal(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Principal must be strictly positive")
        return v

    @field_validator("annual_interest_rate_percent")
    @classmethod
    def validate_non_negative_rate(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Interest rate cannot be negative")
        return v

    @field_validator("tenure_months")
    @classmethod
    def validate_positive_tenure(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Tenure months must be strictly positive")
        return v


class SIPCalculateRequest(BaseModel):
    """Request payload for pure SIP projection endpoint."""

    monthly_contribution: Decimal = Field(..., description="Monthly contribution amount")
    expected_annual_return_percent: Decimal = Field(..., description="Expected annual return percentage")
    duration_years: Decimal = Field(..., description="Investment duration in years")
    contribution_frequency: str = Field(default="MONTHLY")

    @field_validator("monthly_contribution")
    @classmethod
    def validate_positive_contribution(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Monthly contribution must be strictly positive")
        return v

    @field_validator("expected_annual_return_percent")
    @classmethod
    def validate_non_negative_return(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("Expected annual return cannot be negative")
        return v

    @field_validator("duration_years")
    @classmethod
    def validate_positive_duration(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Duration in years must be strictly positive")
        return v


class FinancialSummaryResponse(BaseModel):
    """Overall user financial summary response."""

    total_income: Decimal
    total_expenses: Decimal
    savings: Decimal
    savings_rate_percent: Optional[Decimal]
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
