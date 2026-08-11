"""
Market Data custom exceptions.
"""

from __future__ import annotations

from app.core.exceptions import DhanSarthiError


class MarketDataError(DhanSarthiError):
    """Base exception for all market data operations."""
    pass


class ProviderTimeoutError(MarketDataError):
    """Raised when the external market data provider request times out."""

    def __init__(self, message: str = "Market data provider request timed out.") -> None:
        super().__init__(message)


class ProviderRateLimitedError(MarketDataError):
    """Raised when the external market data provider returns a rate limit error (e.g. HTTP 429)."""

    def __init__(self, message: str = "Market data provider rate limit exceeded.") -> None:
        super().__init__(message)


class ProviderUnavailableError(MarketDataError):
    """Raised when the external market data provider is unreachable or down."""

    def __init__(self, message: str = "Market data provider is temporarily unavailable.") -> None:
        super().__init__(message)


class InvalidSymbolError(MarketDataError):
    """Raised when the supplied ticker symbol or mutual fund scheme is invalid/malformed."""

    def __init__(self, message: str = "The supplied financial symbol is invalid.") -> None:
        super().__init__(message)


class DataNotFoundError(MarketDataError):
    """Raised when the provider succeeds but returns no data for the symbol."""

    def __init__(self, message: str = "Requested market data was not found.") -> None:
        super().__init__(message)


class ProviderAuthError(MarketDataError):
    """Raised when the external provider returns an authentication or API key error."""

    def __init__(self, message: str = "Market data provider authentication failed.") -> None:
        super().__init__(message)


class InvalidProviderResponseError(MarketDataError):
    """Raised when the external provider response payload is malformed or invalid."""

    def __init__(self, message: str = "Received an invalid response from the market data provider.") -> None:
        super().__init__(message)
