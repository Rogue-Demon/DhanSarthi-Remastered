"""
Base abstract interfaces for external financial data providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from app.market_data.schemas import (
    StockQuote,
    StockSearchResult,
    MutualFundNAV,
    MutualFundSearchResult,
    IndexQuote,
    ExchangeRate,
    InterestRate,
)


class StockDataProvider(ABC):
    """Interface for stock quote and search data providers."""

    @abstractmethod
    async def get_quote(self, symbol: str, exchange: Optional[str] = None) -> StockQuote:
        """
        Retrieve a normalized current stock quote.
        """
        pass

    @abstractmethod
    async def search_stocks(self, query: str) -> List[StockSearchResult]:
        """
        Search for stock ticker symbols.
        """
        pass


class MutualFundDataProvider(ABC):
    """Interface for mutual fund NAV and search providers."""

    @abstractmethod
    async def get_nav(self, scheme_id: str) -> MutualFundNAV:
        """
        Retrieve a normalized current mutual fund NAV.
        """
        pass

    @abstractmethod
    async def search_funds(self, query: str) -> List[MutualFundSearchResult]:
        """
        Search for mutual fund schemes.
        """
        pass


class CurrencyDataProvider(ABC):
    """Interface for foreign exchange currency rate providers."""

    @abstractmethod
    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate:
        """
        Retrieve a normalized currency exchange rate.
        """
        pass


class IndexDataProvider(ABC):
    """Interface for market index quote providers."""

    @abstractmethod
    async def get_index_quote(self, index_name: str) -> IndexQuote:
        """
        Retrieve a normalized market index quote.
        """
        pass


class InterestRateProvider(ABC):
    """Interface for central bank reference/interest rate providers."""

    @abstractmethod
    async def get_interest_rate(self, country: str, type_name: str) -> InterestRate:
        """
        Retrieve a central bank reference or lending rate.
        """
        pass
