"""
Dialect-aware Vector TypeDecorator for SQLAlchemy.

Compiles to native pgvector ``Vector(dim)`` on PostgreSQL databases and falls
back to ``JSON`` on SQLite for in-memory unit testing.
"""

from __future__ import annotations

from typing import Any, List, Optional
from sqlalchemy.types import JSON, TypeDecorator
from pgvector.sqlalchemy import Vector


_PGVECTOR_ENABLED: bool = False


def enable_pgvector() -> None:
    """Flag that pgvector extension is verified enabled in database."""
    global _PGVECTOR_ENABLED
    _PGVECTOR_ENABLED = True


class VectorType(TypeDecorator):
    """SQLAlchemy TypeDecorator for vector embeddings."""

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 384) -> None:
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and _PGVECTOR_ENABLED:
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Optional[List[float]], dialect: Any) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return [float(x) for x in value]
        return value
