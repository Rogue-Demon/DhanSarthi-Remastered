"""
Market Data Service for managing caching, fallback providers, and API rate limits.
"""

from __future__ import annotations

import asyncio
import contextvars
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.market_data.exceptions import (
    MarketDataError,
    InvalidSymbolError,
    ProviderUnavailableError,
    DataNotFoundError,
)
from app.market_data.schemas import (
    StockQuote,
    StockSearchResult,
    MutualFundNAV,
    MutualFundSearchResult,
    IndexQuote,
    ExchangeRate,
    InterestRate,
)
from app.market_data.cache import MarketDataCache
from app.market_data.providers.mock import MockMarketDataProvider
from app.market_data.providers.alphavantage import AlphaVantageProvider
from app.market_data.providers.mfapi import MFAPIProvider
from app.market_data.providers.frankfurter import FrankfurterProvider
from app.models.enums import InvestmentType
from app.models.investment import Investment


# Context variable to count provider API calls per request
provider_calls_count = contextvars.ContextVar("provider_calls_count", default=0)
MAX_PROVIDER_CALLS_PER_REQUEST = 10

# Whitelist patterns to block arbitrary URLs or malicious inputs
SYMBOL_WHITELIST_REGEX = re.compile(r"^[A-Za-z0-9\.\-\:]{1,30}$")
SCHEME_WHITELIST_REGEX = re.compile(r"^[0-9]{1,15}$")


class MarketDataService:
    """
    Central orchestrator for fetching live financial data with caching, limit tracking, and fallback.
    """

    def __init__(self, cache: Optional[MarketDataCache] = None) -> None:
        self.cache = cache or MarketDataCache()
        self.mock_provider = MockMarketDataProvider()
        
        # Initialize configured providers
        # 1. Stock Provider
        if settings.stock_data_provider == "alphavantage" and settings.stock_data_api_key:
            self.stock_provider = AlphaVantageProvider(settings.stock_data_api_key)
        else:
            self.stock_provider = self.mock_provider

        # 2. Mutual Fund Provider
        if settings.mutual_fund_provider == "mfapi":
            self.mutual_fund_provider = MFAPIProvider()
        else:
            self.mutual_fund_provider = self.mock_provider

        # 3. Currency Provider
        if settings.fx_provider == "frankfurter":
            self.fx_provider = FrankfurterProvider()
        elif settings.fx_provider == "alphavantage" and settings.stock_data_api_key:
            self.fx_provider = AlphaVantageProvider(settings.stock_data_api_key)
        else:
            self.fx_provider = self.mock_provider

        # 4. Index Provider
        # We use Mock index provider as default/approved provider
        self.index_provider = self.mock_provider

        # 5. Interest Rate Provider
        # We use Mock interest rate provider as default/approved provider
        self.interest_rate_provider = self.mock_provider

    def _increment_call_count(self) -> None:
        """
        Track and limit the number of external API calls in the current request flow.
        """
        count = provider_calls_count.get()
        if count >= MAX_PROVIDER_CALLS_PER_REQUEST:
            raise MarketDataError(
                f"Market data request rejected: exceeded limit of {MAX_PROVIDER_CALLS_PER_REQUEST} provider calls per request."
            )
        provider_calls_count.set(count + 1)

    def _validate_symbol(self, symbol: str, is_mutual_fund: bool = False) -> None:
        """
        Sanitize input symbols to prevent arbitrary HTTP urls or command injection.
        """
        symbol_cleaned = symbol.strip()
        if not symbol_cleaned:
            raise InvalidSymbolError("Symbol cannot be empty.")
        
        if is_mutual_fund:
            if not SCHEME_WHITELIST_REGEX.match(symbol_cleaned):
                raise InvalidSymbolError(f"Invalid mutual fund scheme ID: '{symbol_cleaned}'. Must be a numeric string.")
        else:
            if not SYMBOL_WHITELIST_REGEX.match(symbol_cleaned):
                raise InvalidSymbolError(f"Invalid stock/index ticker symbol: '{symbol_cleaned}'.")

    def _classify_freshness(self, timestamp: datetime, provider: str) -> str:
        """
        Map metadata update time to one of standard states: REAL_TIME, DELAYED, RECENT, STALE, UNKNOWN.
        """
        if "mock" in provider:
            return "REAL_TIME"
        
        now = datetime.now(timezone.utc)
        ts_utc = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        
        age_seconds = (now - ts_utc).total_seconds()
        if age_seconds < 0:
            return "REAL_TIME"
        elif age_seconds <= 900:  # 15 minutes
            return "REAL_TIME"
        elif age_seconds <= 86400:  # 24 hours
            return "DELAYED"
        else:
            return "STALE"

    async def get_stock_quote(self, symbol: str, exchange: Optional[str] = None) -> StockQuote:
        self._validate_symbol(symbol)
        
        # Check cache
        cached = self.cache.get("stock", symbol, settings.market_data_cache_ttl_stock)
        if cached:
            # Check if cached data became stale relative to original timestamp
            cached.freshness = self._classify_freshness(cached.timestamp, cached.provider)
            return cached

        # Execute provider call with fallback
        self._increment_call_count()
        try:
            quote = await self.stock_provider.get_quote(symbol, exchange)
        except (ProviderUnavailableError, MarketDataError) as exc:
            # Fall back to Mock Provider
            if self.stock_provider != self.mock_provider:
                quote = await self.mock_provider.get_quote(symbol, exchange)
                quote.provider = f"{quote.provider} (fallback)"
            else:
                raise exc

        quote.freshness = self._classify_freshness(quote.timestamp, quote.provider)
        self.cache.set("stock", symbol, quote)
        return quote

    async def search_stocks(self, query: str) -> List[StockSearchResult]:
        # Validate query string briefly (no urls)
        if "/" in query or "?" in query or "http" in query:
            raise InvalidSymbolError("Invalid search query.")
        
        try:
            return await self.stock_provider.search_stocks(query)
        except Exception:
            if self.stock_provider != self.mock_provider:
                return await self.mock_provider.search_stocks(query)
            raise

    async def get_mutual_fund_nav(self, scheme_id: str) -> MutualFundNAV:
        self._validate_symbol(scheme_id, is_mutual_fund=True)
        
        # Check cache
        cached = self.cache.get("nav", scheme_id, settings.market_data_cache_ttl_nav)
        if cached:
            return cached

        # Execute provider call with fallback
        self._increment_call_count()
        try:
            nav_data = await self.mutual_fund_provider.get_nav(scheme_id)
        except (ProviderUnavailableError, MarketDataError) as exc:
            # Fall back to Mock Provider
            if self.mutual_fund_provider != self.mock_provider:
                nav_data = await self.mock_provider.get_nav(scheme_id)
                nav_data.provider = f"{nav_data.provider} (fallback)"
            else:
                raise exc

        # Convert date to datetime at midnight UTC for classification
        nav_datetime = datetime.combine(nav_data.nav_date, datetime.min.time(), tzinfo=timezone.utc)
        nav_data.freshness = self._classify_freshness(nav_datetime, nav_data.provider)
        self.cache.set("nav", scheme_id, nav_data)
        return nav_data

    async def search_funds(self, query: str) -> List[MutualFundSearchResult]:
        if "/" in query or "?" in query or "http" in query:
            raise InvalidSymbolError("Invalid search query.")
        
        try:
            return await self.mutual_fund_provider.search_funds(query)
        except Exception:
            if self.mutual_fund_provider != self.mock_provider:
                return await self.mock_provider.search_funds(query)
            raise

    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate:
        # Validate currency code formatting
        if len(base_currency) != 3 or len(quote_currency) != 3:
            raise InvalidSymbolError("Currency codes must be 3 characters.")
        
        cache_key = f"{base_currency}/{quote_currency}"
        cached = self.cache.get("fx", cache_key, settings.market_data_cache_ttl_fx)
        if cached:
            cached.freshness = self._classify_freshness(cached.timestamp, cached.provider)
            return cached

        self._increment_call_count()
        try:
            rate = await self.fx_provider.get_exchange_rate(base_currency, quote_currency)
        except (ProviderUnavailableError, MarketDataError) as exc:
            if self.fx_provider != self.mock_provider:
                rate = await self.mock_provider.get_exchange_rate(base_currency, quote_currency)
                rate.provider = f"{rate.provider} (fallback)"
            else:
                raise exc

        rate.freshness = self._classify_freshness(rate.timestamp, rate.provider)
        self.cache.set("fx", cache_key, rate)
        return rate

    async def get_market_index(self, index_name: str) -> IndexQuote:
        self._validate_symbol(index_name)
        
        cached = self.cache.get("index", index_name, settings.market_data_cache_ttl_index)
        if cached:
            cached.freshness = self._classify_freshness(cached.timestamp, cached.provider)
            return cached

        self._increment_call_count()
        try:
            quote = await self.index_provider.get_index_quote(index_name)
        except (ProviderUnavailableError, MarketDataError) as exc:
            if self.index_provider != self.mock_provider:
                quote = await self.mock_provider.get_index_quote(index_name)
                quote.provider = f"{quote.provider} (fallback)"
            else:
                raise exc

        quote.freshness = self._classify_freshness(quote.timestamp, quote.provider)
        self.cache.set("index", index_name, quote)
        return quote

    async def get_interest_rate(self, country: str, type_name: str) -> InterestRate:
        # Validate parameters
        if len(country) != 2:
            raise InvalidSymbolError("Country code must be 2 characters.")
        
        cache_key = f"{country}/{type_name}"
        cached = self.cache.get("rate", cache_key, settings.market_data_cache_ttl_rate)
        if cached:
            return cached

        self._increment_call_count()
        try:
            rate = await self.interest_rate_provider.get_interest_rate(country, type_name)
        except (ProviderUnavailableError, MarketDataError) as exc:
            if self.interest_rate_provider != self.mock_provider:
                rate = await self.mock_provider.get_interest_rate(country, type_name)
                rate.provider = f"{rate.provider} (fallback)"
            else:
                raise exc

        rate_datetime = datetime.combine(rate.effective_date, datetime.min.time(), tzinfo=timezone.utc)
        rate.freshness = self._classify_freshness(rate_datetime, rate.provider)
        self.cache.set("rate", cache_key, rate)
        return rate

    async def calculate_estimated_portfolio(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Calculate user's portfolio estimated value based on live price/NAV feed.
        Does NOT persist or overwrite current_value or database fields (Fully Immutable).
        """
        # Fetch user's active holdings
        holdings = db.query(Investment).filter(Investment.user_id == user_id).all()
        
        items = []
        total_stored_value = Decimal("0")
        total_estimated_value = Decimal("0")

        for h in holdings:
            meta = h.investment_metadata or {}
            symbol = meta.get("ticker_symbol") or meta.get("scheme_id")
            
            # Default fallback to stored valuation
            est_price = None
            est_value = h.current_value
            freshness = "UNKNOWN"
            prov = "stored_record"
            as_of = h.updated_at.isoformat() if h.updated_at else datetime.now(timezone.utc).isoformat()

            if h.quantity and h.quantity > Decimal("0") and symbol:
                try:
                    if h.investment_type == InvestmentType.STOCK:
                        quote = await self.get_stock_quote(symbol)
                        est_price = quote.price
                        est_value = h.quantity * est_price
                        freshness = quote.freshness
                        prov = quote.provider
                        as_of = quote.data_as_of
                    elif h.investment_type == InvestmentType.MUTUAL_FUND:
                        nav_data = await self.get_mutual_fund_nav(symbol)
                        est_price = nav_data.nav
                        est_value = h.quantity * est_price
                        freshness = nav_data.freshness
                        prov = nav_data.provider
                        as_of = nav_data.nav_date.isoformat()
                except Exception:
                    # Graceful degradation if live quote fails: fall back to stored record values
                    pass

            total_stored_value += h.current_value
            total_estimated_value += est_value

            items.append({
                "investment_id": h.id,
                "name": h.name,
                "type": h.investment_type,
                "symbol": symbol,
                "quantity": h.quantity,
                "stored_value": h.current_value,
                "estimated_price": est_price,
                "estimated_value": est_value,
                "difference": est_value - h.current_value,
                "freshness": freshness,
                "provider": prov,
                "price_as_of": as_of,
            })

        diff = total_estimated_value - total_stored_value
        return {
            "user_id": user_id,
            "total_stored_value": total_stored_value,
            "total_estimated_value": total_estimated_value,
            "difference": diff,
            "difference_percent": (diff / total_stored_value * Decimal("100")).quantize(Decimal("0.01")) if total_stored_value > 0 else Decimal("0"),
            "items": items,
        }
