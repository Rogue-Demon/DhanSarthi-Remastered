"""Income model — recurring and non-recurring user income sources."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IncomeFrequency
from app.models.mixins import SoftDeleteMixin, TimestampMixin, pk_column


class Income(Base, TimestampMixin, SoftDeleteMixin):
    """A user income record.

    Represents any income source: salary, freelance, rental, scholarship,
    allowance, business income, interest, etc.

    Design decisions:
    - ``category`` is a free-form string (not an enum) so new income
      categories can be introduced without schema migrations.  The UI layer
      may enforce a controlled list if desired.
    - ``source`` names the specific origin (employer name, client, platform).
    - ``frequency`` uses the IncomeFrequency enum for the recurring pattern.
    - ``deleted_at`` enables soft deletion — income history is preserved
      for financial analysis even after a user removes a record.

    NUMERIC(18, 2): 18 significant digits, 2 decimal places — sufficient
    for INR amounts without floating-point precision loss.
    """

    __tablename__ = "incomes"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_incomes_amount_non_negative"),
        Index("ix_incomes_user_id_income_date", "user_id", "income_date"),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    frequency: Mapped[IncomeFrequency] = mapped_column(
        SAEnum(IncomeFrequency, native_enum=False, validate_strings=True, length=15),
        nullable=False,
        default=IncomeFrequency.MONTHLY,
    )
    income_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="incomes"
    )

    def __repr__(self) -> str:
        return f"<Income id={self.id} user_id={self.user_id} amount={self.amount} source={self.source!r}>"
