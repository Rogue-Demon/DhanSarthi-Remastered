"""
Mutual Fund API data provider adapter for api.mfapi.in (Indian Mutual Funds).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List
import httpx

from app.market_data.base import MutualFundDataProvider
from app.market_data.schemas import MutualFundNAV, MutualFundSearchResult
from app.market_data.exceptions import (
    ProviderTimeoutError,
    ProviderUnavailableError,
    InvalidSymbolError,
    DataNotFoundError,
    InvalidProviderResponseError,
)


class MFAPIProvider(MutualFundDataProvider):
    """
    Adapter for the free and public AMFI Mutual Fund API (api.mfapi.in).
    """

    def __init__(self, timeout_seconds: int = 15) -> None:
        self._timeout = timeout_seconds
        self._base_url = "https://api.mfapi.in/mf"

    async def get_nav(self, scheme_id: str) -> MutualFundNAV:
        # Scheme ID must be a numeric string
        if not scheme_id.isdigit():
            raise InvalidSymbolError(f"Scheme ID must be numeric AMFI code: {scheme_id}")

        url = f"{self._base_url}/{scheme_id}"
        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    raise DataNotFoundError(f"Scheme {scheme_id} was not found on mfapi.in")
                if resp.status_code != 200:
                    raise ProviderUnavailableError(f"mfapi.in returned HTTP status {resp.status_code}")
                
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Timeout calling Mutual Fund NAV API: {str(exc)}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(f"Error calling Mutual Fund NAV API: {str(exc)}") from exc

        # If data is empty or meta is missing
        meta = data.get("meta")
        nav_data = data.get("data")
        
        if not meta or not nav_data:
            raise DataNotFoundError(f"No NAV data found for scheme ID: {scheme_id}")

        # The latest NAV is at index 0
        latest_entry = nav_data[0]
        nav_str = latest_entry.get("nav")
        date_str = latest_entry.get("date")

        if not nav_str or not date_str:
            raise InvalidProviderResponseError(f"Malformed NAV entry returned for scheme: {scheme_id}")

        try:
            nav = Decimal(nav_str)
            # Parse dd-mm-yyyy date
            nav_date = datetime.strptime(date_str, "%d-%m-%Y").date()
            scheme_name = meta.get("scheme_name", f"Mutual Fund Scheme {scheme_id}")

            return MutualFundNAV(
                scheme_id=scheme_id,
                scheme_name=scheme_name,
                nav=nav,
                currency="INR",
                nav_date=nav_date,
                freshness="RECENT",  # NAVs are updated daily
                provider="mfapi",
                source="AMFI Mutual Fund NAV API",
            )
        except Exception as exc:
            raise InvalidProviderResponseError(f"Failed to parse NAV response: {str(exc)}") from exc

    async def search_funds(self, query: str) -> List[MutualFundSearchResult]:
        url = f"{self._base_url}/search"
        try:
            async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
                resp = await client.get(url, params={"q": query})
                if resp.status_code != 200:
                    raise ProviderUnavailableError(f"mfapi.in returned HTTP status {resp.status_code}")
                
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Timeout calling Mutual Fund Search API: {str(exc)}") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(f"Error calling Mutual Fund Search API: {str(exc)}") from exc

        results: List[MutualFundSearchResult] = []
        if isinstance(data, list):
            for item in data:
                scheme_id = str(item.get("schemeCode"))
                scheme_name = item.get("schemeName")
                if scheme_id and scheme_name:
                    results.append(
                        MutualFundSearchResult(
                            scheme_id=scheme_id,
                            scheme_name=scheme_name,
                            provider="mfapi",
                        )
                    )
        return results
