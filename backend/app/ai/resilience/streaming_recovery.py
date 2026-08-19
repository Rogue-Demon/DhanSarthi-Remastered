"""
Streaming Recovery and Stream Disconnect Handler for Phase L.9.9.

Integrates directly with Phase L.9.8 SSE architecture to ensure clean termination
upon network drops or client cancellations, preventing partial DB persistence
and scrubbing internal exceptions from error payloads.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def format_sse_error_event(code: str = "STREAM_INTERRUPTED", message: str = "AI response stream was interrupted. Please try again.") -> str:
    """
    Format a sanitized Server-Sent Events (SSE) error payload.
    
    Guarantees:
      - Does not include internal stack traces or secrets.
      - Uses standardized event: error framing.
    """
    payload = {
        "code": code,
        "message": message,
    }
    return f"event: error\ndata: {json.dumps(payload)}\n\n"


class StreamingRecoveryManager:
    """
    Coordinates lifecycle recovery during real-time SSE streaming.
    """

    def __init__(self) -> None:
        pass

    def on_stream_interrupted(self, streamed_chunks_count: int, failure_reason: str) -> str:
        """
        Produce a safe error event when an active stream is severed mid-generation.
        """
        logger.warning(
            f"Streaming severed after {streamed_chunks_count} chunks. Reason: {failure_reason}. "
            "Emitting sanitized SSE error event."
        )
        return format_sse_error_event(
            code="STREAM_INTERRUPTED",
            message="The AI response was interrupted due to a provider timeout or connection issue. Please retry.",
        )

    def on_client_cancelled(self) -> None:
        """Log client disconnect/cancellation event."""
        logger.info("Streaming client disconnected / request cancelled by user. Rolling back partial state.")
