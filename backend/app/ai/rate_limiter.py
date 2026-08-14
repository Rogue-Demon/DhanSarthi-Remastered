"""
Lightweight in-memory sliding-window rate limiter for AI generation endpoints.

Protects the AI Advisor against rapid repeated requests, client loops,
and excessive upstream LLM provider costs.
"""

from __future__ import annotations

import time
from collections import defaultdict
from fastapi import HTTPException, status

from app.core.config import settings


class AIRateLimiter:
    """Sliding-window rate limiter scoped per authenticated user ID."""

    def __init__(
        self,
        max_requests: int | None = None,
        window_seconds: int | None = None,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[int, list[float]] = defaultdict(list)

    @property
    def max_requests(self) -> int:
        if self._max_requests is not None:
            return self._max_requests
        return settings.ai_rate_limit_requests

    @property
    def window_seconds(self) -> int:
        if self._window_seconds is not None:
            return self._window_seconds
        return settings.ai_rate_limit_window_seconds

    def check_rate_limit(self, user_id: int) -> None:
        """
        Record a request for user_id and raise HTTP 429 if the sliding-window limit is exceeded.
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        # Clean timestamps older than the window
        timestamps = [t for t in self._requests[user_id] if t > cutoff]
        self._requests[user_id] = timestamps

        if len(timestamps) >= self.max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(oldest + self.window_seconds - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"AI request rate limit exceeded ({self.max_requests} requests per "
                    f"{self.window_seconds}s). Please wait before trying again."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        self._requests[user_id].append(now)

    def reset(self) -> None:
        """Clear all tracking state (used in testing)."""
        self._requests.clear()


ai_rate_limiter = AIRateLimiter()


def enforce_ai_rate_limit(user_id: int) -> None:
    """Convenience helper to check rate limit for a user."""
    ai_rate_limiter.check_rate_limit(user_id)
