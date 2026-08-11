"""
Unit tests for MarketDataService features including limits, fallbacks, and deduplication.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.market_data.exceptions import MarketDataError, ProviderUnavailableError
from app.market_data.service import MarketDataService, provider_calls_count
from app.market_data.providers.mock import MockMarketDataProvider
from app.market_data.providers.alphavantage import AlphaVantageProvider


@pytest.mark.anyio
async def test_service_enforces_api_call_limits():
    service = MarketDataService()
    
    # Initialize count to 9 (near limit)
    provider_calls_count.set(9)
    
    # Tenth call succeeds
    await service.get_stock_quote("RELIANCE.NS")
    
    # Eleventh call fails
    with pytest.raises(MarketDataError) as exc:
        await service.get_stock_quote("TCS.NS")
    assert "exceeded limit" in str(exc.value)

    # Reset count for safety
    provider_calls_count.set(0)


@pytest.mark.anyio
async def test_service_performs_deduplication_via_caching():
    service = MarketDataService()
    
    # Reset count
    provider_calls_count.set(0)

    # First call: cache miss, increments count
    await service.get_stock_quote("RELIANCE.NS")
    assert provider_calls_count.get() == 1

    # Second call: cache hit, does NOT increment count
    await service.get_stock_quote("RELIANCE.NS")
    assert provider_calls_count.get() == 1


@pytest.mark.anyio
async def test_service_fallback_to_mock_on_real_provider_failure():
    # Force real provider configuration to fail
    with patch("app.core.config.settings.stock_data_provider", "alphavantage"), \
         patch("app.core.config.settings.stock_data_api_key", "dummy"):
        
        service = MarketDataService()
        
        # Verify it is configured with AlphaVantageProvider
        assert isinstance(service.stock_provider, AlphaVantageProvider)
        
        # Mock get_quote to raise ProviderUnavailableError
        with patch.object(AlphaVantageProvider, "get_quote", side_effect=ProviderUnavailableError("API offline")):
            # Retrieve quote: should fall back to mock
            quote = await service.get_stock_quote("RELIANCE.NS")
            
            assert "fallback" in quote.provider
            assert quote.symbol == "RELIANCE.NS"
