"""
Phase L.9.6 — Intelligent Response Cache & In-Flight Deduplication Package.
"""

from app.ai.cache.cache_policy import CacheEligibilityPolicy
from app.ai.cache.cache_key import CacheKeyBuilder
from app.ai.cache.inflight import InFlightDeduplicator, get_inflight_deduplicator
from app.ai.cache.response_cache import (
    IntelligentResponseCache,
    ResponseCacheEntry,
    EducationalResponseCache,
    get_response_cache,
    get_educational_cache,
)

__all__ = [
    "CacheEligibilityPolicy",
    "CacheKeyBuilder",
    "InFlightDeduplicator",
    "get_inflight_deduplicator",
    "IntelligentResponseCache",
    "ResponseCacheEntry",
    "EducationalResponseCache",
    "get_response_cache",
    "get_educational_cache",
]
