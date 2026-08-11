"""
Mock financial market data provider for tests and development.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from app.market_data.base import (
    StockDataProvider,
    MutualFundDataProvider,
    CurrencyDataProvider,
    IndexDataProvider,
    InterestRateProvider,
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
from app.market_data.exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitedError,
    ProviderUnavailableError,
    InvalidSymbolError,
    DataNotFoundError,
)


class MockMarketDataProvider(
    StockDataProvider,
    MutualFundDataProvider,
    CurrencyDataProvider,
    IndexDataProvider,
    InterestRateProvider,
):
    """
    Mock provider implementing all provider interfaces.
    """

    async def get_quote(self, symbol: str, exchange: Optional[str] = None) -> StockQuote:
        symbol_upper = symbol.upper()
        
        # Simulated errors for testing
        if "TIMEOUT" in symbol_upper:
            raise ProviderTimeoutError(f"Mock timeout for stock quote retrieval of {symbol}")
        if "RATELIMIT" in symbol_upper:
            raise ProviderRateLimitedError(f"Mock rate limit for stock quote retrieval of {symbol}")
        if "UNAVAILABLE" in symbol_upper:
            raise ProviderUnavailableError(f"Mock service unavailable for stock quote retrieval of {symbol}")
        if "INVALID" in symbol_upper:
            raise InvalidSymbolError(f"Mock invalid symbol requested: {symbol}")
        if "NOTFOUND" in symbol_upper:
            raise DataNotFoundError(f"Mock data not found: {symbol}")

        # Default fallback values for mock data
        price = Decimal("2450.50")
        name = "Mock Stock"
        change = Decimal("15.20")
        change_pct = Decimal("0.62")

        if "RELIANCE" in symbol_upper:
            price = Decimal("2550.00")
            change = Decimal("25.50")
            change_pct = Decimal("1.01")
        elif "TCS" in symbol_upper:
            price = Decimal("3400.00")
            change = Decimal("-45.00")
            change_pct = Decimal("-1.31")
        elif "INFY" in symbol_upper:
            price = Decimal("1450.00")
            change = Decimal("5.50")
            change_pct = Decimal("0.38")

        now = datetime.now(timezone.utc)
        return StockQuote(
            symbol=symbol,
            exchange=exchange or "NSE",
            price=price,
            currency="INR",
            timestamp=now,
            data_as_of=now.isoformat(),
            freshness="RECENT",
            provider="mock_stock_provider",
            source="Mock Stock API",
            previous_close=price - change,
            change=change,
            change_percent=change_pct,
            market_status="OPEN",
        )

    async def search_stocks(self, query: str) -> List[StockSearchResult]:
        q = query.upper()
        results = [
            StockSearchResult(symbol="RELIANCE.NS", company_name="Reliance Industries Ltd.", exchange="NSE", currency="INR", provider="mock_stock_provider"),
            StockSearchResult(symbol="TCS.NS", company_name="Tata Consultancy Services Ltd.", exchange="NSE", currency="INR", provider="mock_stock_provider"),
            StockSearchResult(symbol="INFY.NS", company_name="Infosys Ltd.", exchange="NSE", currency="INR", provider="mock_stock_provider"),
        ]
        return [r for r in results if q in r.symbol or q in r.company_name.upper()]

    async def get_nav(self, scheme_id: str) -> MutualFundNAV:
        sid = scheme_id.upper()
        
        if "TIMEOUT" in sid:
            raise ProviderTimeoutError()
        if "NOTFOUND" in sid:
            raise DataNotFoundError()

        nav = Decimal("78.50")
        name = "Mock Mutual Fund Scheme"

        if scheme_id == "119063":
            nav = Decimal("125.40")
            name = "SBI Bluechip Fund - Direct Growth"
        elif scheme_id == "102873":
            nav = Decimal("310.20")
            name = "HDFC Top 100 Fund - Growth"

        return MutualFundNAV(
            scheme_id=scheme_id,
            scheme_name=name,
            nav=nav,
            currency="INR",
            nav_date=date.today(),
            freshness="RECENT",
            provider="mock_mf_provider",
            source="Mock NAV API",
        )

    async def search_funds(self, query: str) -> List[MutualFundSearchResult]:
        q = query.upper()
        results = [
            MutualFundSearchResult(scheme_id="119063", scheme_name="SBI Bluechip Fund - Direct Growth", provider="mock_mf_provider"),
            MutualFundSearchResult(scheme_id="102873", scheme_name="HDFC Top 100 Fund - Growth", provider="mock_mf_provider"),
        ]
        return [r for r in results if q in r.scheme_name.upper() or q in r.scheme_id]

    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate:
        bc = base_currency.upper()
        qc = quote_currency.upper()

        if "TIMEOUT" in bc or "TIMEOUT" in qc:
            raise ProviderTimeoutError()

        rate = Decimal("83.25")
        if bc == "USD" and qc == "INR":
            rate = Decimal("83.25")
        elif bc == "EUR" and qc == "INR":
            rate = Decimal("89.50")
        elif bc == "GBP" and qc == "INR":
            rate = Decimal("104.20")
        elif bc == qc:
            rate = Decimal("1.0")
        else:
            # Arbitrary rate fallback
            rate = Decimal("1.25")

        now = datetime.now(timezone.utc)
        return ExchangeRate(
            base_currency=base_currency,
            quote_currency=quote_currency,
            rate=rate,
            timestamp=now,
            data_as_of=now.isoformat(),
            freshness="RECENT",
            provider="mock_fx_provider",
        )

    async def get_index_quote(self, index_name: str) -> IndexQuote:
        name = index_name.upper()

        if "TIMEOUT" in name:
            raise ProviderTimeoutError()

        value = Decimal("72000.00")
        change = Decimal("250.00")
        change_pct = Decimal("0.35")

        if "SENSEX" in name:
            value = Decimal("72500.00")
            change = Decimal("350.00")
            change_pct = Decimal("0.48")
        elif "NIFTY" in name or "NIFTY_50" in name:
            value = Decimal("22000.00")
            change = Decimal("120.00")
            change_pct = Decimal("0.55")

        now = datetime.now(timezone.utc)
        return IndexQuote(
            index_name=index_name,
            value=value,
            change=change,
            change_percent=change_pct,
            timestamp=now,
            data_as_of=now.isoformat(),
            freshness="RECENT",
            provider="mock_index_provider",
        )

    async def get_interest_rate(self, country: str, type_name: str) -> InterestRate:
        c = country.upper()
        t = type_name.upper()

        if "TIMEOUT" in c or "TIMEOUT" in t:
            raise ProviderTimeoutError()

        rate = Decimal("6.50")
        inst = "Central Bank"

        if c == "IN":
            inst = "Reserve Bank of India"
            if "REPO" in t:
                rate = Decimal("6.50")
            elif "REVERSE" in t:
                rate = Decimal("3.35")
            elif "SAVINGS" in t:
                rate = Decimal("3.00")
        elif c == "US":
            inst = "Federal Reserve"
            if "FED" in t or "POLICY" in t:
                rate = Decimal("5.25")

        return InterestRate(
            country=country,
            type_name=type_name,
            rate=rate,
            effective_date=date.today(),
            freshness="RECENT",
            provider="mock_rate_provider",
            institution=inst,
        )
