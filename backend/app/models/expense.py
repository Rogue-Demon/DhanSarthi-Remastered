"""Expense model — user spending records."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ExpenseFrequency
from app.models.mixins import SoftDeleteMixin, TimestampMixin, pk_column


class Expense(Base, TimestampMixin, SoftDeleteMixin):
    """A user expense record.

    Covers any spending category: rent, food, transport, education,
    entertainment, utilities, healthcare, shopping, EMI payments, etc.

    Design decisions:
    - ``category`` is a free-form string (not an enum) for the same reason
      as Income — new expense categories should not require migrations.
    - ``frequency`` is nullable; one-time expenses have no recurrence.
    - ``deleted_at`` enables soft deletion for historical integrity.

    Soft delete means the record is hidden from the UI but retained in the
    database for cash-flow analysis and reporting.
    """

    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_expenses_amount_non_negative"),
        Index("ix_expenses_user_id_expense_date", "user_id", "expense_date"),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency: Mapped[ExpenseFrequency | None] = mapped_column(
        SAEnum(ExpenseFrequency, native_enum=False, validate_strings=True, length=15),
        nullable=True,
    )

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="expenses"
    )

    def __repr__(self) -> str:
        return f"<Expense id={self.id} user_id={self.user_id} amount={self.amount} category={self.category!r}>"
