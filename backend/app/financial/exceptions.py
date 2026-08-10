"""
DhanSarthi Financial Engine Exceptions.

All domain exceptions raised by the Financial Engine inherit from
``FinancialEngineError``.  These exceptions are pure domain errors and are
independent of FastAPI or HTTP status codes.
"""

from __future__ import annotations


class FinancialEngineError(Exception):
    """Base exception for all financial engine calculation errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidFinancialInput(FinancialEngineError):
    """Raised when calculation inputs violate domain constraints (e.g., negative money amounts)."""

    pass


class InvalidLoanParameters(FinancialEngineError):
    """Raised when loan parameters are invalid (e.g., non-positive principal, negative tenure)."""

    pass


class InvalidInvestmentParameters(FinancialEngineError):
    """Raised when investment inputs are invalid (e.g., negative contribution, zero duration)."""

    pass


class InsufficientFinancialData(FinancialEngineError):
    """Raised when required data for a metric is missing or insufficient (e.g. division by zero)."""

    pass


class InvalidCalculationPeriod(FinancialEngineError):
    """Raised when a date range or period is invalid."""

    pass
