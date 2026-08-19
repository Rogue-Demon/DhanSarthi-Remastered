"""
Phase L.9.6 — Intelligent Response Cache for DhanSarthi AI Advisor.

Provides bounded, thread/async-safe LRU caching with configurable TTL,
knowledge/model version invalidation, and comprehensive observability counters.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import datetime
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from app.ai.router import QueryIntent
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResponseCacheEntry:
    """
    Immutable cached response payload including citations, quality score, and metadata.
    """
    response_text: str
    citations: List[Dict[str, Any]] = field(default_factory=list)
    quality: Dict[str, Any] = field(default_factory=dict)
    model_id: str = ""
    created_at_mono: float = field(default_factory=time.monotonic)
    created_timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    expires_at_mono: float = 0.0
    version: str = "v1"
    prompt_tokens: int = 0
    generated_tokens: int = 0

    @property
    def age_ms(self) -> float:
        """Return the age of this cache entry in milliseconds."""
        return max(0.0, (time.monotonic() - self.created_at_mono) * 1000.0)

    @property
    def is_expired(self) -> bool:
        """Check if this entry has passed its expiration time."""
        return time.monotonic() > self.expires_at_mono


class IntelligentResponseCache:
    """
    Thread-safe / async-safe bounded LRU response cache with TTL expiration.
    """

    def __init__(self) -> None:
        self._store: OrderedDict[str, ResponseCacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits: int = 0
        self._misses: int = 0
        self._writes: int = 0
        self._evictions: int = 0
        self._expirations: int = 0

    def get(self, key: str) -> Optional[ResponseCacheEntry]:
        """
        Retrieve a cached response entry if it exists and is not expired.
        """
        if not (settings.ai_response_cache_enabled and settings.ai_cache_educational_enabled):
            with self._lock:
                self._misses += 1
            return None

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired:
                self._store.pop(key, None)
                self._expirations += 1
                self._misses += 1
                logger.debug("Cache entry expired for key %s…", key[:16])
                return None

            # Mark as recently used (LRU)
            self._store.move_to_end(key)
            self._hits += 1
            logger.debug("Cache hit for key %s… (age=%.1fms)", key[:16], entry.age_ms)
            return entry

    def put(
        self,
        key: str,
        response_text: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        quality: Optional[Dict[str, Any]] = None,
        model_id: str = "",
        prompt_tokens: int = 0,
        generated_tokens: int = 0,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Store a validated response entry in the cache.
        """
        if not (settings.ai_response_cache_enabled and settings.ai_cache_educational_enabled):
            return False

        if not response_text or not response_text.strip():
            return False

        effective_ttl = ttl_seconds or settings.ai_response_cache_ttl_seconds
        expires_at = time.monotonic() + effective_ttl

        entry = ResponseCacheEntry(
            response_text=response_text,
            citations=citations or [],
            quality=quality or {},
            model_id=model_id or settings.ai_model,
            expires_at_mono=expires_at,
            version=settings.ai_response_cache_version,
            prompt_tokens=prompt_tokens,
            generated_tokens=generated_tokens,
        )

        with self._lock:
            max_entries = settings.ai_response_cache_max_entries
            if len(self._store) >= max_entries and key not in self._store:
                oldest_key, _ = next(iter(self._store.items()))
                self._store.pop(oldest_key, None)
                self._evictions += 1
                logger.debug("Cache evicted oldest entry (capacity=%d)", max_entries)

            self._store[key] = entry
            self._store.move_to_end(key)
            self._writes += 1
            logger.debug("Cache stored key %s… (TTL=%ds)", key[:16], effective_ttl)
            return True

    def invalidate(self, key: Optional[str] = None) -> None:
        """
        Invalidate a specific key or all entries in the cache.
        """
        with self._lock:
            if key is not None:
                self._store.pop(key, None)
            else:
                self._store.clear()
            logger.debug("Cache invalidated (key=%s)", key)

    def clear(self) -> None:
        """Alias for invalidate() clearing all entries."""
        self.invalidate()

    @property
    def size(self) -> int:
        """Current number of items in cache."""
        with self._lock:
            return len(self._store)

    def get_stats(self) -> Dict[str, Any]:
        """Return cache performance statistics."""
        with self._lock:
            total_lookups = self._hits + self._misses
            hit_rate = round((self._hits / total_lookups) * 100.0, 2) if total_lookups > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "writes": self._writes,
                "evictions": self._evictions,
                "expirations": self._expirations,
                "size": len(self._store),
                "max_entries": settings.ai_response_cache_max_entries,
                "ttl_seconds": settings.ai_response_cache_ttl_seconds,
                "hit_rate_pct": hit_rate,
                "version": settings.ai_response_cache_version,
            }


# ----------------------------------------------------------------------
# Backward-compatibility layer for Phase L.7.2 EducationalResponseCache
# ----------------------------------------------------------------------

class EducationalResponseCache:
    """
    Adapter preserving 100% backward compatibility for L.7.2 interface while
    delegating to IntelligentResponseCache.
    """

    def __init__(self, inner: Optional[IntelligentResponseCache] = None) -> None:
        self._inner = inner or IntelligentResponseCache()

    def get(
        self,
        query: str,
        model_name: str,
        max_tokens: int,
        intent: QueryIntent,
        scope: Optional[str] = None,
        has_personal_context: bool = False,
        has_live_market_data: bool = False,
    ) -> Optional[str]:
        from app.ai.cache.cache_policy import CacheEligibilityPolicy
        from app.ai.cache.cache_key import CacheKeyBuilder

        if not CacheEligibilityPolicy.is_eligible(
            query=query,
            intent=intent,
            scope=scope,
            has_personal_context=has_personal_context,
            has_live_market_data=has_live_market_data,
        ):
            return None

        key = CacheKeyBuilder.build_key(
            query=query,
            model_id=model_name,
            max_tokens_budget=max_tokens,
            scope=scope,
        )
        entry = self._inner.get(key)
        return entry.response_text if entry else None

    def put(
        self,
        query: str,
        model_name: str,
        max_tokens: int,
        intent: QueryIntent,
        scope: Optional[str],
        has_personal_context: bool,
        has_live_market_data: bool,
        response_text: str,
    ) -> bool:
        from app.ai.cache.cache_policy import CacheEligibilityPolicy
        from app.ai.cache.cache_key import CacheKeyBuilder

        if not CacheEligibilityPolicy.is_eligible(
            query=query,
            intent=intent,
            scope=scope,
            has_personal_context=has_personal_context,
            has_live_market_data=has_live_market_data,
        ):
            return False

        key = CacheKeyBuilder.build_key(
            query=query,
            model_id=model_name,
            max_tokens_budget=max_tokens,
            scope=scope,
        )
        return self._inner.put(key=key, response_text=response_text, model_id=model_name)

    def invalidate(self) -> None:
        self._inner.invalidate()

    def clear(self) -> None:
        self._inner.clear()

    @property
    def size(self) -> int:
        return self._inner.size


# Module-level singletons
_response_cache = IntelligentResponseCache()
_educational_cache = EducationalResponseCache(inner=_response_cache)


def get_response_cache() -> IntelligentResponseCache:
    """Return the global response cache singleton."""
    return _response_cache


def get_educational_cache() -> EducationalResponseCache:
    """Return the backward-compatible educational cache singleton."""
    return _educational_cache
