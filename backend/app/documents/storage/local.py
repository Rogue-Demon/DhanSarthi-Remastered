"""
Local filesystem document storage for development.

Files are stored under: {base_path}/{user_segment}/{storage_key}

Path traversal protection: storage_key must match a strict pattern and
is always validated before constructing filesystem paths.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from app.documents.storage.base import DocumentStorage


_SAFE_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_\-/\.]+$")


class LocalDocumentStorage(DocumentStorage):
    """Development-mode local filesystem storage."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """Resolve a storage key to a safe filesystem path."""
        if not _SAFE_KEY_PATTERN.match(key):
            raise ValueError(f"Invalid storage key: {key}")
        resolved = (self._base / key).resolve()
        # Prevent path traversal
        if not str(resolved).startswith(str(self._base.resolve())):
            raise ValueError("Path traversal detected in storage key.")
        return resolved

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    async def get(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        path = self._resolve(key)
        return path.exists()
