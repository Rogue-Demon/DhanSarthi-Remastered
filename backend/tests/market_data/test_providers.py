"""
Unit tests for market data provider adapters.
"""

from __future__ import annotations

import json
from decimal import Decimal
from datetime import date, datetime, timezone
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
from app.market_data.exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitedError,
    ProviderUnavailableError,
    InvalidSymbolError,
    DataNotFoundError,
)
from app.market_data.providers.mock import MockMarketDataProvider
from app.market_data.providers.alphavantage import AlphaVantageProvider
from app.market_data.providers.mfapi import MFAPIProvider
from app.market_data.providers.frankfurter import FrankfurterProvider


@pytest.mark.anyio
async def test_mock_provider_returns_valid_data():
    provider = MockMarketDataProvider()
    
    # Test Stock
    quote = await provider.get_quote("RELIANCE.NS")
    assert quote.symbol == "RELIANCE.NS"
    assert quote.price == Decimal("2550.00")
    assert quote.currency == "INR"
    assert quote.provider == "mock_stock_provider"
    
    # Test MF NAV
    nav = await provider.get_nav("119063")
    assert nav.scheme_id == "119063"
    assert nav.nav == Decimal("125.40")
    assert nav.currency == "INR"
    assert nav.provider == "mock_mf_provider"

    # Test FX Rate
    rate = await provider.get_exchange_rate("USD", "INR")
    assert rate.base_currency == "USD"
    assert rate.quote_currency == "INR"
    assert rate.rate == Decimal("83.25")

    # Test Index
    idx = await provider.get_index_quote("SENSEX")
    assert idx.value == Decimal("72500.00")

    # Test Interest Rate
    ir = await provider.get_interest_rate("IN", "Repo Rate")
    assert ir.rate == Decimal("6.50")


@pytest.mark.anyio
async def test_mock_provider_simulates_errors():
    provider = MockMarketDataProvider()

    with pytest.raises(ProviderTimeoutError):
        await provider.get_quote("TIMEOUT")

    with pytest.raises(ProviderRateLimitedError):
        await provider.get_quote("RATELIMIT")

    with pytest.raises(ProviderUnavailableError):
        await provider.get_quote("UNAVAILABLE")

    with pytest.raises(InvalidSymbolError):
        await provider.get_quote("INVALID")

    with pytest.raises(DataNotFoundError):
        await provider.get_quote("NOTFOUND")


@pytest.mark.anyio
async def test_mfapi_provider_success():
    provider = MFAPIProvider()
    mock_resp = {
        "meta": {
            "scheme_name": "SBI Bluechip Fund"
        },
        "data": [
            {"date": "08-03-2024", "nav": "89.26120"},
            {"date": "07-03-2024", "nav": "88.50000"}
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_resp)
        nav = await provider.get_nav("119063")
        assert nav.scheme_id == "119063"
        assert nav.scheme_name == "SBI Bluechip Fund"
        assert nav.nav == Decimal("89.26120")
        assert nav.nav_date == date(2024, 3, 8)


@pytest.mark.anyio
async def test_frankfurter_provider_success():
    provider = FrankfurterProvider()
    mock_resp = {
        "amount": 1.0,
        "base": "USD",
        "date": "2024-03-08",
        "rates": {"INR": 82.68}
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_resp)
        rate = await provider.get_exchange_rate("USD", "INR")
        assert rate.base_currency == "USD"
        assert rate.quote_currency == "INR"
        assert rate.rate == Decimal("82.68")


@pytest.mark.anyio
async def test_alphavantage_provider_success():
    provider = AlphaVantageProvider("dummy_key")
    mock_resp = {
        "Global Quote": {
            "01. symbol": "IBM",
            "05. price": "182.0100",
            "08. previous close": "184.4200",
            "09. change": "-2.4100",
            "10. change percent": "-1.3068%"
        }
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_resp)
        quote = await provider.get_quote("IBM")
        assert quote.symbol == "IBM"
        assert quote.price == Decimal("182.0100")
        assert quote.change_percent == Decimal("-1.3068")
