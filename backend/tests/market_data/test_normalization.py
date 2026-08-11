"""
Unit tests for data normalization across different adapters.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone, date
import pytest
from unittest.mock import MagicMock, patch

from app.market_data.providers.alphavantage import AlphaVantageProvider
from app.market_data.providers.mfapi import MFAPIProvider


@pytest.mark.anyio
async def test_normalization_produces_identical_schemas():
    # Test stock response normalization from AlphaVantage
    av_provider = AlphaVantageProvider("dummy")
    av_raw = {
        "Global Quote": {
            "01. symbol": "RELIANCE.NS",
            "05. price": "2450.50",
            "08. previous close": "2435.30",
            "09. change": "15.20",
            "10. change percent": "0.6241%"
        }
    }
    
    # We want to verify it parses correctly to StockQuote schema
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: av_raw)
        quote = await av_provider.get_quote("RELIANCE.NS")
        
        assert quote.symbol == "RELIANCE.NS"
        assert quote.price == Decimal("2450.50")
        assert quote.previous_close == Decimal("2435.30")
        assert quote.change == Decimal("15.20")
        assert quote.change_percent == Decimal("0.6241")
        assert quote.currency == "USD"
        assert quote.provider == "alphavantage"

    # Test Mutual Fund NAV normalization from MFAPI
    mf_provider = MFAPIProvider()
    mf_raw = {
        "meta": {
            "scheme_name": "SBI Bluechip Fund"
        },
        "data": [
            {"date": "08-03-2024", "nav": "89.26"}
        ]
    }
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: mf_raw)
        nav = await mf_provider.get_nav("119063")
        
        assert nav.scheme_id == "119063"
        assert nav.scheme_name == "SBI Bluechip Fund"
        assert nav.nav == Decimal("89.26")
        assert nav.nav_date == date(2024, 3, 8)
        assert nav.currency == "INR"
        assert nav.provider == "mfapi"
