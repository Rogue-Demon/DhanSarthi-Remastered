"""
Abstract safety validator interface for evaluating advisor inputs and outputs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.ai.schemas.advisor import AIContext


class AISafetyValidator(ABC):
    """Abstraction for enforcing safety constraints before exposing LLM outputs to users."""

    @abstractmethod
    def validate_response(self, response: str, context: AIContext) -> None:
        """
        Check that the LLM response adheres to DhanSarthi safety rules.

        Validation rules:
          - Rejects any response containing secrets (passwords, JWT tokens, keys).
          - Detects and rejects commands to perform autonomous transactions.
          - Rejects inappropriate guarantees about stock returns or loan approval.

        Args:
            response: The candidate text response returned by the LLM.
            context: The AIContext payload sent to build the prompt.

        Raises:
            AISafetyError: When safety boundary is violated.
        """
        pass
