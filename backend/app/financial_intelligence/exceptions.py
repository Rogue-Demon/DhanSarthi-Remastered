"""
Financial Intelligence and Decision Engine custom exceptions.
"""

from __future__ import annotations

from app.core.exceptions import DhanSarthiError


class FinancialIntelligenceError(DhanSarthiError):
    """Base exception for all financial intelligence operations."""
    pass


class FinancialIntelligenceAccessDeniedError(FinancialIntelligenceError):
    """Raised when a user attempts to access resources or run scenarios on data they do not own."""

    def __init__(self, message: str = "Access denied. You do not own this resource.") -> None:
        super().__init__(message)


class InvalidScenarioError(FinancialIntelligenceError):
    """Raised when scenario parameters are invalid or out of bounds."""

    def __init__(self, message: str = "Invalid scenario parameters.") -> None:
        super().__init__(message)


class InsufficientDataError(FinancialIntelligenceError):
    """Raised when a calculation cannot be performed due to insufficient financial context."""

    def __init__(self, message: str = "Insufficient data to perform calculations.") -> None:
        super().__init__(message)
