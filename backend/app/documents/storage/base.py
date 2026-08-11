"""
Abstract document storage interface.

The Document Intelligence layer depends on this abstraction — never on
a specific filesystem or cloud implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class DocumentStorage(ABC):
    """Abstract interface for secure document file storage."""

    @abstractmethod
    async def save(self, key: str, data: bytes, content_type: str) -> str:
        """Save file data under the given storage key.

        Args:
            key: Unique storage identifier (UUID-based, never original filename).
            data: Raw file bytes.
            content_type: MIME type of the file.

        Returns:
            str: The storage key (may be the same as input key).
        """
        pass

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """Retrieve raw file bytes by storage key.

        Raises:
            FileNotFoundError: If the key does not exist.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the stored file. Idempotent — does not raise if missing."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check whether a file exists at the given storage key."""
        pass
