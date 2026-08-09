"""Transaction model — actual financial movement events."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, Enum as SAEnum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TransactionType
from app.models.mixins import SoftDeleteMixin, TimestampMixin, pk_column


class Transaction(Base, TimestampMixin, SoftDeleteMixin):
    """A financial movement event.

    This is distinct from Income and Expense which represent financial
    *classifications*.  A Transaction records the actual movement of money —
    from a bank account, digital wallet, or external transfer.

    Distinction:
        Income/Expense → financial classification of a financial state
        Transaction    → an actual timestamped movement/event of funds

    The ``source`` field is a free-form string today, deliberately left open
    to link to future Account/Wallet/BankAccount entities without a schema
    rewrite.  When an Account model is introduced, a nullable FK column can
    be added alongside this string field via migration.

    ``category`` is nullable because a transfer may not have an income or
    expense category (it is a movement between accounts, not a spend/earn).
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_transactions_amount_non_negative"),
        Index("ix_transactions_user_id_transaction_date", "user_id", "transaction_date"),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, native_enum=False, validate_strings=True, length=10),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="transactions"
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} user_id={self.user_id} "
            f"type={self.transaction_type} amount={self.amount}>"
        )
