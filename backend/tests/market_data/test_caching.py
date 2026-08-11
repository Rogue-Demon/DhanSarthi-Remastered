"""
Unit tests for market data caching and freshness classification.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app.market_data.cache import MarketDataCache
from app.market_data.service import MarketDataService
from app.market_data.schemas import StockQuote


def test_cache_hits_misses_and_ttl():
    cache = MarketDataCache()
    now = datetime.now(timezone.utc)
    
    quote1 = StockQuote(
        symbol="RELIANCE.NS",
        price=Decimal("2500.00"),
        timestamp=now,
        data_as_of=now.isoformat(),
        freshness="REAL_TIME",
        provider="mock",
        source="test",
    )

    # Cache miss
    assert cache.get("stock", "RELIANCE.NS", ttl_seconds=60) is None

    # Cache set and hit
    cache.set("stock", "RELIANCE.NS", quote1)
    cached = cache.get("stock", "RELIANCE.NS", ttl_seconds=60)
    assert cached is not None
    assert cached.price == Decimal("2500.00")

    # Cache expiry (simulate TTL)
    cached_expired = cache.get("stock", "RELIANCE.NS", ttl_seconds=-1)
    assert cached_expired is None


def test_freshness_classification():
    service = MarketDataService()
    now = datetime.now(timezone.utc)

    # 1. Under 15 minutes -> REAL_TIME (for non-mock)
    fresh = service._classify_freshness(now - timedelta(minutes=5), "real_provider")
    assert fresh == "REAL_TIME"

    # 2. Between 15m and 24h -> DELAYED
    delayed = service._classify_freshness(now - timedelta(hours=3), "real_provider")
    assert delayed == "DELAYED"

    # 3. Older than 24h -> STALE
    stale = service._classify_freshness(now - timedelta(days=2), "real_provider")
    assert stale == "STALE"

    # 4. Mock provider always returns REAL_TIME
    mock_fresh = service._classify_freshness(now - timedelta(days=20), "mock_stock_provider")
    assert mock_fresh == "REAL_TIME"
