"""
FastAPI router for Live Financial Market Data Layer.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user_id, get_market_data_service
from app.market_data.service import MarketDataService
from app.market_data.exceptions import (
    MarketDataError,
    InvalidSymbolError,
    ProviderUnavailableError,
    DataNotFoundError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
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


router = APIRouter(prefix="/market", tags=["market"])


def _handle_market_exceptions(exc: Exception) -> None:
    """Helper to convert market data exceptions to FastAPI HTTPExceptions."""
    if isinstance(exc, InvalidSymbolError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    elif isinstance(exc, DataNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    elif isinstance(exc, ProviderRateLimitedError):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)
    elif isinstance(exc, (ProviderUnavailableError, ProviderTimeoutError)):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message)
    elif isinstance(exc, MarketDataError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    raise exc


@router.get("/stocks/search", response_model=List[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1, max_length=50),
    service: MarketDataService = Depends(get_market_data_service),
) -> List[StockSearchResult]:
    """Search for stock symbols matching the query string."""
    try:
        return await service.search_stocks(q)
    except Exception as exc:
        _handle_market_exceptions(exc)


@router.get("/stocks/{symbol}", response_model=StockQuote)
async def get_stock_quote(
    symbol: str,
    exchange: Optional[str] = Query(default=None, max_length=20),
    service: MarketDataService = Depends(get_market_data_service),
) -> StockQuote:
    """Retrieve a live or cached stock quote for the specified symbol."""
    try:
        return await service.get_stock_quote(symbol, exchange)
    except Exception as exc:
        _handle_market_exceptions(exc)


@router.get("/mutual-funds/search", response_model=List[MutualFundSearchResult])
async def search_mutual_funds(
    q: str = Query(..., min_length=1, max_length=50),
    service: MarketDataService = Depends(get_market_data_service),
) -> List[MutualFundSearchResult]:
    """Search for mutual fund schemes matching the query."""
    try:
        return await service.search_funds(q)
    except Exception as exc:
        _handle_market_exceptions(exc)


@router.get("/mutual-funds/{scheme_id}/nav", response_model=MutualFundNAV)
async def get_mutual_fund_nav(
    scheme_id: str,
    service: MarketDataService = Depends(get_market_data_service),
) -> MutualFundNAV:
    """Retrieve the latest Net Asset Value (NAV) for a mutual fund scheme."""
    try:
        return await service.get_mutual_fund_nav(scheme_id)
    except Exception as exc:
        _handle_market_exceptions(exc)


@router.get("/fx/{base}/{quote}", response_model=ExchangeRate)
async def get_exchange_rate(
    base: str,
    quote: str,
    service: MarketDataService = Depends(get_market_data_service),
) -> ExchangeRate:
    """Retrieve the current foreign exchange currency conversion rate."""
    try:
        return await service.get_exchange_rate(base, quote)
    except Exception as exc:
        _handle_market_exceptions(exc)


@router.get("/indices/{index_name}", response_model=IndexQuote)
async def get_index_quote(
    index_name: str,
    service: MarketDataService = Depends(get_market_data_service),
) -> IndexQuote:
    """Retrieve the current quote for a major market benchmark/index."""
    try:
        return await service.get_market_index(index_name)
    except Exception as exc:
        _handle_market_exceptions(exc)


@router.get("/interest-rates/{country}/{type_name}", response_model=InterestRate)
async def get_interest_rate(
    country: str,
    type_name: str,
    service: MarketDataService = Depends(get_market_data_service),
) -> InterestRate:
    """Retrieve central bank interest/policy rates for a given country."""
    try:
        return await service.get_interest_rate(country, type_name)
    except Exception as exc:
        _handle_market_exceptions(exc)


@router.get("/portfolio/estimated")
async def get_estimated_portfolio_valuation(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    service: MarketDataService = Depends(get_market_data_service),
):
    """
    Calculate the estimated current valuation of the authenticated user's active stock/fund portfolio.
    This operation is fully read-only and does not modify database records.
    """
    try:
        return await service.calculate_estimated_portfolio(user_id=user_id, db=db)
    except Exception as exc:
        _handle_market_exceptions(exc)
