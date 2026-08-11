"""
In-memory caching mechanism for market data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


class MarketDataCache:
    """
    In-memory cache for market data entries to prevent excessive API calls.
    """

    def __init__(self) -> None:
        self._store: Dict[Tuple[str, str], Tuple[Any, datetime]] = {}

    def get(self, category: str, key: str, ttl_seconds: int) -> Optional[Any]:
        """
        Retrieve a cached item if it exists and has not expired.
        """
        composite_key = (category.lower(), key.upper())
        entry = self._store.get(composite_key)
        if not entry:
            return None

        data, cached_at = entry
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        if age > ttl_seconds:
            # Cache expired
            del self._store[composite_key]
            return None

        return data

    def set(self, category: str, key: str, data: Any) -> None:
        """
        Store an item in the cache with the current timestamp.
        """
        composite_key = (category.lower(), key.upper())
        self._store[composite_key] = (data, datetime.now(timezone.utc))

    def clear(self) -> None:
        """
        Clear all entries in the cache.
        """
        self._store.clear()
