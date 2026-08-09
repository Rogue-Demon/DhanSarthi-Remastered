"""Liability model — user debts and obligations for net worth calculation."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Enum as SAEnum, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import LiabilityType
from app.models.mixins import TimestampMixin, pk_column


class Liability(Base, TimestampMixin):
    """A user liability or debt obligation reducing net worth.

    Captures general liabilities including credit card balances, personal
    debts not tracked in detail, and business obligations.

    Relationship with Loan model:
    - Liability captures a *snapshot* of an outstanding obligation.
      It is suitable for simple debts or obligations where payment history
      and EMI tracking are not required.
    - Loan model captures a detailed loan with tenure, EMI, interest rate,
      and a full repayment history via LoanPayment records.
    - Avoid duplicating the same debt in both Liability and Loan.

    ``interest_rate`` — annual rate as NUMERIC(6, 4), e.g. 0.1800 = 18%.
    ``liability_metadata`` — flexible details stored as JSON:
      e.g. {"bank": "HDFC", "card_last4": "4321"} for credit cards.
    """

    __tablename__ = "liabilities"
    __table_args__ = (
        CheckConstraint(
            "outstanding_amount >= 0",
            name="ck_liabilities_outstanding_amount_non_negative",
        ),
        CheckConstraint(
            "interest_rate >= 0",
            name="ck_liabilities_interest_rate_non_negative",
        ),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    liability_type: Mapped[LiabilityType] = mapped_column(
        SAEnum(LiabilityType, native_enum=False, validate_strings=True, length=20),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    liability_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="liabilities"
    )

    def __repr__(self) -> str:
        return (
            f"<Liability id={self.id} user_id={self.user_id} "
            f"type={self.liability_type} amount={self.outstanding_amount}>"
        )
