"""
Pydantic schemas for normalized live market data models.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class StockQuote(BaseModel):
    """Normalized stock price quote schema."""

    symbol: str = Field(..., description="Ticker symbol (e.g. RELIANCE.NS, TCS.NS)")
    exchange: Optional[str] = Field(default=None, description="Market exchange name (e.g. NSE, BSE)")
    price: Decimal = Field(..., description="Current stock price")
    currency: str = Field(default="INR", description="Quote currency")
    timestamp: datetime = Field(..., description="Provider price update timestamp")
    data_as_of: str = Field(..., description="Human readable timestamp (e.g. ISO string)")
    freshness: str = Field(..., description="Freshness classification: REAL_TIME, DELAYED, RECENT, STALE, UNKNOWN")
    provider: str = Field(..., description="Name of the supplying API/provider")
    source: str = Field(..., description="Information source name")
    previous_close: Optional[Decimal] = Field(default=None, description="Previous close price")
    change: Optional[Decimal] = Field(default=None, description="Absolute daily change amount")
    change_percent: Optional[Decimal] = Field(default=None, description="Daily change percentage")
    market_status: str = Field(default="UNKNOWN", description="Market status: OPEN, CLOSED, PRE_MARKET, POST_MARKET, UNKNOWN")


class StockSearchResult(BaseModel):
    """Normalized search results for a stock ticker query."""

    symbol: str
    company_name: str
    exchange: str
    currency: str
    provider: str


class MutualFundNAV(BaseModel):
    """Normalized Mutual Fund Net Asset Value (NAV) schema."""

    scheme_id: str = Field(..., description="Unique scheme identifier (AMFI code or symbol)")
    scheme_name: str = Field(..., description="Full descriptive name of the mutual fund scheme")
    nav: Decimal = Field(..., description="Net Asset Value per unit")
    currency: str = Field(default="INR", description="NAV currency")
    nav_date: date = Field(..., description="Date the NAV applies to")
    freshness: str = Field(..., description="Freshness classification: REAL_TIME, DELAYED, RECENT, STALE, UNKNOWN")
    provider: str = Field(..., description="Name of the supplying API/provider")
    source: str = Field(..., description="Information source name")


class MutualFundSearchResult(BaseModel):
    """Normalized mutual fund search query result item."""

    scheme_id: str
    scheme_name: str
    provider: str


class IndexQuote(BaseModel):
    """Normalized quote for major market index (e.g. SENSEX, NIFTY 50)."""

    index_name: str = Field(..., description="Name/Symbol of index")
    value: Decimal = Field(..., description="Current index value")
    change: Optional[Decimal] = Field(default=None, description="Index absolute change")
    change_percent: Optional[Decimal] = Field(default=None, description="Index percentage change")
    timestamp: datetime = Field(..., description="Last update timestamp")
    data_as_of: str = Field(..., description="Human readable timestamp")
    freshness: str = Field(..., description="Freshness classification")
    provider: str = Field(..., description="Provider name")


class ExchangeRate(BaseModel):
    """Normalized foreign currency exchange rate schema."""

    base_currency: str = Field(..., description="Base currency code (e.g. USD)")
    quote_currency: str = Field(..., description="Target quote currency code (e.g. INR)")
    rate: Decimal = Field(..., description="Exchange conversion rate")
    timestamp: datetime = Field(..., description="Exchange rate update timestamp")
    data_as_of: str = Field(..., description="Human readable timestamp")
    freshness: str = Field(..., description="Freshness classification")
    provider: str = Field(..., description="Provider name")


class InterestRate(BaseModel):
    """Normalized interest rate schema."""

    country: str = Field(..., description="Country code (e.g. IN)")
    type_name: str = Field(..., description="Interest rate type (e.g. Repo Rate, Bank Rate)")
    rate: Decimal = Field(..., description="Interest rate percentage")
    effective_date: date = Field(..., description="Effective date of this rate change")
    freshness: str = Field(..., description="Freshness classification")
    provider: str = Field(..., description="Provider name")
    institution: str = Field(..., description="Governing institution (e.g. RBI)")
