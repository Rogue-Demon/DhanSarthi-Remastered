"""Budget model — spending limits by category and time period."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BudgetPeriod
from app.models.mixins import TimestampMixin, pk_column


class Budget(Base, TimestampMixin):
    """A user budget allocation for a spending category within a period.

    Represents a spending limit the user sets for a category (e.g. Food,
    Entertainment) over a defined time period (monthly, weekly, yearly, or
    a custom date range).

    ``category`` — free-form string matching the Expense category taxonomy.
    ``period``   — the recurrence pattern for this budget.
    ``end_date`` — nullable; for CUSTOM period budgets with a fixed end date.
                   MONTHLY / WEEKLY / YEARLY budgets may leave this null.

    Budget vs. actual spending analysis belongs to the Financial Engine.
    """

    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),
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
    period: Mapped[BudgetPeriod] = mapped_column(
        SAEnum(BudgetPeriod, native_enum=False, validate_strings=True, length=10),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="budgets"
    )

    def __repr__(self) -> str:
        return (
            f"<Budget id={self.id} user_id={self.user_id} "
            f"category={self.category!r} period={self.period}>"
        )
