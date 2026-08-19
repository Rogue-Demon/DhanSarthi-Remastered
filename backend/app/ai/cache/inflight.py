"""
Phase L.9.6 — Async In-Flight Request Deduplication for DhanSarthi AI Advisor.

Coalesces identical concurrent eligible requests so only one LLM inference is
executed while other callers await and share the same validated result.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class InFlightDeduplicator:
    """
    Registry that coalesces simultaneous in-flight operations matching the same key.
    """

    def __init__(self) -> None:
        self._inflight: Dict[str, Tuple[asyncio.Future[Any], List[bool]]] = {}
        self._lock = asyncio.Lock()
        self._deduplications_count: int = 0

    async def execute_or_join(
        self,
        key: str,
        coro_factory: Callable[[], Awaitable[T]],
    ) -> Tuple[T, bool]:
        """
        Execute coro_factory() or join an existing in-flight future for the same key.

        Returns:
            Tuple[T, bool]: (result, was_deduplicated)
            where was_deduplicated is True if this caller shared an in-flight request.
        """
        future: Optional[asyncio.Future[Any]] = None
        is_owner = False

        async with self._lock:
            if key in self._inflight:
                # Concurrent request already in flight: join it!
                future, waiters = self._inflight[key]
                waiters.append(True)
                self._deduplications_count += 1
                is_owner = False
                logger.debug("InFlight deduplication joined for key %s…", key[:16])
            else:
                # First caller: become owner
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                self._inflight[key] = (future, [])
                is_owner = True
                logger.debug("InFlight deduplication owner registered for key %s…", key[:16])

        if not is_owner:
            # Await the owner's result
            assert future is not None
            result = await future
            return result, True

        # Owner executes the actual generation coroutine
        try:
            result = await coro_factory()
            if not future.done():
                future.set_result(result)
            return result, False
        except BaseException as exc:
            if not future.done():
                async with self._lock:
                    entry = self._inflight.get(key)
                    has_waiters = bool(entry and len(entry[1]) > 0)
                if has_waiters:
                    future.set_exception(exc)
                else:
                    future.cancel()
            raise
        finally:
            async with self._lock:
                self._inflight.pop(key, None)
                logger.debug("InFlight key cleaned up: %s…", key[:16])

    @property
    def inflight_count(self) -> int:
        """Current number of distinct in-flight keys."""
        return len(self._inflight)

    @property
    def deduplications_count(self) -> int:
        """Total number of deduplicated (coalesced) requests served."""
        return self._deduplications_count

    def clear(self) -> None:
        """Clear all in-flight entries (used for testing resets)."""
        self._inflight.clear()
        self._deduplications_count = 0


_GLOBAL_INFLIGHT_DEDUPLICATOR: Optional[InFlightDeduplicator] = None


def get_inflight_deduplicator() -> InFlightDeduplicator:
    """Return singleton InFlightDeduplicator instance."""
    global _GLOBAL_INFLIGHT_DEDUPLICATOR
    if _GLOBAL_INFLIGHT_DEDUPLICATOR is None:
        _GLOBAL_INFLIGHT_DEDUPLICATOR = InFlightDeduplicator()
    return _GLOBAL_INFLIGHT_DEDUPLICATOR
