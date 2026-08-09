"""Loan and LoanPayment models — detailed loan lifecycle tracking."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import LoanStatus, LoanType
from app.models.mixins import TimestampMixin, pk_column


class Loan(Base, TimestampMixin):
    """A detailed user loan record.

    Designed for comprehensive loan tracking including EMI, tenure, and
    interest parameters.  The Financial Engine will use these fields for
    EMI calculation, amortization, and affordability analysis in a later
    phase.  No calculations are performed in this model.

    vs. Liability model:
    - Loan  : detailed product — lender, tenure, EMI, payment history
    - Liability: snapshot — outstanding amount, no payment tracking

    ``tenure``           : total loan tenure in months
    ``remaining_tenure`` : months remaining (nullable — may be unknown at entry)
    ``emi``              : monthly EMI amount (nullable — calculated later)
    ``interest_rate``    : annual rate as NUMERIC(6, 4), e.g. 0.0875 = 8.75%

    Cascade: LoanPayment records are deleted when the Loan is deleted
    (payment records without a parent loan are meaningless).
    """

    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint(
            "principal_amount > 0", name="ck_loans_principal_amount_positive"
        ),
        CheckConstraint(
            "outstanding_amount >= 0",
            name="ck_loans_outstanding_amount_non_negative",
        ),
        CheckConstraint(
            "interest_rate >= 0", name="ck_loans_interest_rate_non_negative"
        ),
        CheckConstraint("tenure > 0", name="ck_loans_tenure_positive"),
        CheckConstraint(
            "remaining_tenure >= 0",
            name="ck_loans_remaining_tenure_non_negative",
        ),
        CheckConstraint("emi >= 0", name="ck_loans_emi_non_negative"),
        Index("ix_loans_user_id_status", "user_id", "status"),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    loan_type: Mapped[LoanType] = mapped_column(
        SAEnum(LoanType, native_enum=False, validate_strings=True, length=15),
        nullable=False,
    )
    lender: Mapped[str] = mapped_column(String(200), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False
    )  # annual, e.g. 0.0875
    tenure: Mapped[int] = mapped_column(Integer, nullable=False)  # months
    remaining_tenure: Mapped[int | None] = mapped_column(Integer, nullable=True)
    emi: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[LoanStatus] = mapped_column(
        SAEnum(LoanStatus, native_enum=False, validate_strings=True, length=10),
        nullable=False,
        default=LoanStatus.ACTIVE,
    )

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="loans"
    )
    payments: Mapped[list[LoanPayment]] = relationship(
        "LoanPayment",
        back_populates="loan",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Loan id={self.id} user_id={self.user_id} "
            f"type={self.loan_type} status={self.status}>"
        )


class LoanPayment(Base):
    """A single loan repayment installment.

    Records each payment made against a Loan, storing both the total amount
    and its breakdown into principal and interest components.  These records
    allow the Financial Engine to compute amortization schedules and
    repayment analysis in future phases.

    ``principal_component`` and ``interest_component`` are nullable because
    they may not be known at time of payment entry and will be populated by
    the Financial Engine.

    Only ``created_at`` is stored — payments are immutable financial events.
    """

    __tablename__ = "loan_payments"
    __table_args__ = (
        CheckConstraint(
            "amount >= 0", name="ck_loan_payments_amount_non_negative"
        ),
        CheckConstraint(
            "principal_component >= 0",
            name="ck_loan_payments_principal_component_non_negative",
        ),
        CheckConstraint(
            "interest_component >= 0",
            name="ck_loan_payments_interest_component_non_negative",
        ),
        CheckConstraint(
            "remaining_balance >= 0",
            name="ck_loan_payments_remaining_balance_non_negative",
        ),
        Index(
            "ix_loan_payments_loan_id_payment_date", "loan_id", "payment_date"
        ),
    )

    id: Mapped[int] = pk_column()
    loan_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("loans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    principal_component: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    interest_component: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    remaining_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    loan: Mapped[Loan] = relationship("Loan", back_populates="payments")

    def __repr__(self) -> str:
        return (
            f"<LoanPayment id={self.id} loan_id={self.loan_id} amount={self.amount}>"
        )
