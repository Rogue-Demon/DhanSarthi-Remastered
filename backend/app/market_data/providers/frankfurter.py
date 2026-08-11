"""
Frankfurter API currency exchange data provider adapter.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import httpx

from app.market_data.base import CurrencyDataProvider
from app.market_data.schemas import ExchangeRate
from app.market_data.exceptions import (
    ProviderTimeoutError,
    ProviderUnavailableError,
    InvalidSymbolError,
    DataNotFoundError,
    InvalidProviderResponseError,
)


class FrankfurterProvider(CurrencyDataProvider):
    """
    Adapter for the free and public Frankfurter FX API (api.frankfurter.app).
    """

    def __init__(self, timeout_seconds: int = 15) -> None:
        self._timeout = timeout_seconds
        self._base_url = "https://api.frankfurter.app/latest"

    async def get_exchange_rate(self, base_currency: str, quote_currency: str) -> ExchangeRate:
        bc = base_currency.upper()
        qc = quote_currency.upper()

        if bc == qc:
            now = datetime.now(timezone.utc)
            return ExchangeRate(
                base_currency=bc,
                quote_currency=qc,
                rate=Decimal("1.0"),
                timestamp=now,
                data_as_of=now.isoformat(),
                freshness="REAL_TIME",
                provider="frankfurter",
            )

        url = f"{self._base_url}"
        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                resp = await client.get(url, params={"from": bc, "to": qc})
                if resp.status_code == 404:
                    raise InvalidSymbolError(f"Unsupported base/quote currency pair: {bc}/{qc}")
                if resp.status_code != 200:
                    raise ProviderUnavailableError(f"Frankfurter returned HTTP status {resp.status_code}")
                
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Timeout calling Frankfurter FX API: {str(exc)}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(f"Error calling Frankfurter FX API: {str(exc)}") from exc

        rates = data.get("rates", {})
        rate_val = rates.get(qc)
        if rate_val is None:
            raise DataNotFoundError(f"Exchange rate from {bc} to {qc} not found.")

        try:
            rate = Decimal(str(rate_val))
            now = datetime.now(timezone.utc)
            return ExchangeRate(
                base_currency=bc,
                quote_currency=qc,
                rate=rate,
                timestamp=now,
                data_as_of=now.isoformat(),
                freshness="RECENT",  # Frankfurter rates are updated once a day around 16:00 CET
                provider="frankfurter",
            )
        except Exception as exc:
            raise InvalidProviderResponseError(f"Failed to parse currency rate: {str(exc)}") from exc
