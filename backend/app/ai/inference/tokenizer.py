"""
Model-Aware Tokenizer Service for DhanSarthi Phase L.8.

Provides thread-safe, lazy-loaded token count estimation and budget truncation
using Hugging Face AutoTokenizer with a character-ratio fallback.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, List, Optional, Union

from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback character-to-token ratio (4.0 chars per token for English/financial text)
_FALLBACK_CHARS_PER_TOKEN: float = 4.0


class LLMTokenizer:
    """Thread-safe, lazy-loaded tokenizer service with offline fallback."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or getattr(settings, "ai_tokenizer_model", settings.ai_model)
        self._tokenizer: Any = None
        self._is_loaded: bool = False
        self._load_failed: bool = False
        self._lock = threading.Lock()

    def _ensure_loaded(self) -> None:
        """Lazily load the Hugging Face AutoTokenizer inside a thread-safe lock."""
        if self._is_loaded or self._load_failed:
            return

        with self._lock:
            if self._is_loaded or self._load_failed:
                return

            try:
                from transformers import AutoTokenizer  # type: ignore

                logger.info(f"Loading LLM tokenizer for model: {self.model_name}")
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._is_loaded = True
            except Exception as exc:
                logger.warning(
                    f"Could not load Hugging Face tokenizer '{self.model_name}' ({exc}). "
                    f"Falling back to character-ratio estimator ({_FALLBACK_CHARS_PER_TOKEN} chars/token)."
                )
                self._load_failed = True
                self._tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Count actual tokens in text, or return ratio estimate if tokenizer unavailable."""
        if not text:
            return 0

        self._ensure_loaded()

        if self._is_loaded and self._tokenizer is not None:
            try:
                tokens = self._tokenizer.encode(text, add_special_tokens=False)
                return len(tokens)
            except Exception:
                pass

        # Fallback ratio counting
        return max(1, int(len(text) / _FALLBACK_CHARS_PER_TOKEN))

    def count_prompt_tokens(self, prompt_content: Union[str, List[dict[str, str]]]) -> int:
        """Count tokens in string prompt or list of chat messages."""
        if isinstance(prompt_content, str):
            return self.count_tokens(prompt_content)

        if isinstance(prompt_content, list):
            total = 0
            for msg in prompt_content:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    total += self.count_tokens(content) + 4  # Overhead per turn
            return max(1, total)

        return 0

    def truncate_to_token_budget(self, text: str, max_tokens: int) -> str:
        """Truncate text so token count does not exceed max_tokens budget."""
        if not text or max_tokens <= 0:
            return ""

        current_tokens = self.count_tokens(text)
        if current_tokens <= max_tokens:
            return text

        self._ensure_loaded()

        if self._is_loaded and self._tokenizer is not None:
            try:
                token_ids = self._tokenizer.encode(text, add_special_tokens=False)
                truncated_ids = token_ids[:max_tokens]
                return self._tokenizer.decode(truncated_ids, skip_special_tokens=True)
            except Exception:
                pass

        # Fallback character length truncation based on ratio
        target_chars = int(max_tokens * _FALLBACK_CHARS_PER_TOKEN)
        return text[:target_chars]


# Global singleton instance for tokenizer reuse
_tokenizer_instance: Optional[LLMTokenizer] = None
_instance_lock = threading.Lock()


def get_tokenizer(model_name: Optional[str] = None) -> LLMTokenizer:
    """Get or create singleton LLMTokenizer instance."""
    global _tokenizer_instance
    if _tokenizer_instance is None:
        with _instance_lock:
            if _tokenizer_instance is None:
                _tokenizer_instance = LLMTokenizer(model_name=model_name)
    return _tokenizer_instance
