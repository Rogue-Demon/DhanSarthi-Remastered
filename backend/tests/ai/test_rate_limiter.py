"""
Unit tests for AI Rate Limiter — Phase D Production Audit.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.ai.rate_limiter import AIRateLimiter, ai_rate_limiter, enforce_ai_rate_limit


class TestAIRateLimiter:
    def setup_method(self):
        ai_rate_limiter.reset()

    def test_allows_under_limit(self):
        limiter = AIRateLimiter(max_requests=5, window_seconds=60)
        user_id = 9991
        for _ in range(5):
            limiter.check_rate_limit(user_id)  # Should not raise

    def test_blocks_exceeding_limit(self):
        limiter = AIRateLimiter(max_requests=3, window_seconds=60)
        user_id = 9992
        for _ in range(3):
            limiter.check_rate_limit(user_id)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check_rate_limit(user_id)
        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers
        assert "rate limit exceeded" in exc_info.value.detail.lower()

    def test_users_are_isolated(self):
        limiter = AIRateLimiter(max_requests=2, window_seconds=60)
        user_a = 9993
        user_b = 9994

        limiter.check_rate_limit(user_a)
        limiter.check_rate_limit(user_a)

        # User A exceeds
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(user_a)

        # User B still has allowance
        limiter.check_rate_limit(user_b)
        limiter.check_rate_limit(user_b)

    def test_enforce_convenience_function(self):
        ai_rate_limiter.reset()
        enforce_ai_rate_limit(1001)  # Should not raise for fresh user
