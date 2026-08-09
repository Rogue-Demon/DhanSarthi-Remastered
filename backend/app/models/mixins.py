"""
Shared SQLAlchemy column mixins for DhanSarthi models.

TimestampMixin  — created_at + updated_at (applied to every model)
SoftDeleteMixin — deleted_at (applied only to Income, Expense, Transaction)

Using ``mapped_column()`` in mixins is the recommended SQLAlchemy 2.0
approach; the column definition is copied to each concrete subclass table.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column


def pk_column():
    """Return a primary key column mapping BigInteger (PostgreSQL identity)

    to Integer on SQLite (for test environment auto-increment compatibility).
    """
    return mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class TimestampMixin:
    """Adds timezone-aware ``created_at`` and ``updated_at`` columns.

    ``created_at`` is set server-side on INSERT via ``server_default``.
    ``updated_at`` is refreshed application-side on every UPDATE via
    SQLAlchemy's ``onupdate`` hook (includes the SQL expression in the
    generated SET clause).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds a nullable ``deleted_at`` timestamp for soft deletion.

    NULL  → record is active.
    NOT NULL → record has been soft-deleted; retain for historical integrity.

    Applied deliberately only to user-facing financial event records
    (Income, Expense, Transaction) where preserving history matters.
    Physical DELETE of these records is discouraged.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
