"""
Alpha Vantage API data provider adapter.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import httpx

from app.market_data.base import StockDataProvider, CurrencyDataProvider
from app.market_data.schemas import StockQuote, StockSearchResult, ExchangeRate
from app.market_data.exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitedError,
    ProviderUnavailableError,
    InvalidSymbolError,
    DataNotFoundError,
    InvalidProviderResponseError,
    ProviderAuthError,
)


class AlphaVantageProvider(StockDataProvider, CurrencyDataProvider):
    """
    Adapter implementation using Alpha Vantage REST APIs.
    """

    def __init__(self, api_key: str, timeout_seconds: int = 15) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._base_url = "https://www.alphavantage.co/query"

    async def _make_request(self, params: dict) -> dict:
        params["apikey"] = self._api_key
        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                resp = await client.get(self._base_url, params=params)
                if resp.status_code == 429:
                    raise ProviderRateLimitedError("Alpha Vantage rate limit exceeded.")
                if resp.status_code != 200:
                    raise ProviderUnavailableError(f"Alpha Vantage returned HTTP status {resp.status_code}.")
                
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Timeout calling Alpha Vantage API: {str(exc)}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(f"Error calling Alpha Vantage API: {str(exc)}") from exc

        # Alpha Vantage returns standard warnings / info in Note or Information fields
        if "Note" in data:
            raise ProviderRateLimitedError(f"Alpha Vantage frequency warning: {data['Note']}")
        if "Error Message" in data:
            raise InvalidSymbolError(f"Alpha Vantage error: {data['Error Message']}")
        if "Information" in data:
            raise ProviderUnavailableError(f"Alpha Vantage information: {data['Information']}")

        return data

    async def get_quote(self, symbol: str, exchange: Optional[str] = None) -> StockQuote:
        data = await self._make_request({"function": "GLOBAL_QUOTE", "symbol": symbol})
        
        quote_data = data.get("Global Quote")
        if not quote_data:
            raise DataNotFoundError(f"No global quote found for symbol: {symbol}")

        # If price key is missing, treat as not found
        price_str = quote_data.get("05. price")
        if not price_str:
            raise DataNotFoundError(f"Empty quote data returned for symbol: {symbol}")

        try:
            price = Decimal(price_str)
            prev_close = Decimal(quote_data.get("08. previous close", "0"))
            change = Decimal(quote_data.get("09. change", "0"))
            
            # Clean change percent string (e.g. "-1.3068%" -> -1.3068)
            change_pct_str = quote_data.get("10. change percent", "0%").replace("%", "")
            change_pct = Decimal(change_pct_str)

            now = datetime.now(timezone.utc)
            return StockQuote(
                symbol=symbol,
                exchange=exchange or "US",
                price=price,
                currency="USD",  # Default AlphaVantage currency for global symbols
                timestamp=now,
                data_as_of=now.isoformat(),
                freshness="DELAYED",  # AlphaVantage free tier is typically delayed
                provider="alphavantage",
                source="Alpha Vantage Global Quote",
                previous_close=prev_close,
                change=change,
                change_percent=change_pct,
                market_status="UNKNOWN",
            )
        except Exception as exc:
            raise InvalidProviderResponseError(f"Failed to parse Alpha Vantage response: {str(exc)}") from exc

    async def search_stocks(self, query: str) -> List[StockSearchResult]:
        data = await self._make_request({"function": "SYMBOL_SEARCH", "keywords": query})
        
        matches = data.get("bestMatches", [])
        results: List[StockSearchResult] = []
        
        for m in matches:
            symbol = m.get("1. symbol")
            name = m.get("2. name")
            region = m.get("4. region", "US")
            currency = m.get("8. currency", "USD")
            if symbol and name:
                results.append(
                    StockSearchResult(
                        symbol=symbol,
                        company_name=name,
                        exchange=region,
                        currency=currency,
                        provider="alphavantage",
                    )
                )
        return results

    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate:
        data = await self._make_request({
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": base_currency,
            "to_currency": quote_currency,
        })

        rate_data = data.get("Realtime Currency Exchange Rate")
        if not rate_data:
            raise DataNotFoundError(f"No exchange rate found from {base_currency} to {quote_currency}")

        rate_str = rate_data.get("5. Exchange Rate")
        if not rate_str:
            raise InvalidProviderResponseError("Exchange rate value is missing in response.")

        try:
            rate = Decimal(rate_str)
            now = datetime.now(timezone.utc)
            return ExchangeRate(
                base_currency=base_currency,
                quote_currency=quote_currency,
                rate=rate,
                timestamp=now,
                data_as_of=now.isoformat(),
                freshness="REAL_TIME",
                provider="alphavantage",
            )
        except Exception as exc:
            raise InvalidProviderResponseError(f"Failed to parse exchange rate: {str(exc)}") from exc
