"""
Phase L.7.2 / Phase L.9.6 — Response Cache Forwarding Module.

Re-exports IntelligentResponseCache and EducationalResponseCache from app.ai.cache.
"""

from app.ai.cache.response_cache import (
    EducationalResponseCache,
    IntelligentResponseCache,
    ResponseCacheEntry,
    get_educational_cache,
    get_response_cache,
)

__all__ = [
    "EducationalResponseCache",
    "IntelligentResponseCache",
    "ResponseCacheEntry",
    "get_educational_cache",
    "get_response_cache",
]
