"""Investment and InvestmentTransaction models."""

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
    JSON,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import InvestmentTransactionType, InvestmentType
from app.models.mixins import TimestampMixin, pk_column


class Investment(Base, TimestampMixin):
    """A user investment holding.

    Supports all DhanSarthi investment types: stocks, mutual funds, SIPs,
    fixed deposits (FD), recurring deposits (RD), bonds, ETFs, and gold.

    Not every field applies to every investment type — nullable fields are
    permitted where the domain genuinely allows missing information:

    Field applicability guide:
    - ``quantity``      : STOCK, ETF, MUTUAL_FUND (shares/units held)
    - ``maturity_date`` : FD, RD, BOND
    - ``interest_rate`` : FD, RD, BOND (annual rate e.g. 0.0750 = 7.5%)
    - ``investment_metadata``: type-specific extras without schema sprawl

    ``principal``     — total amount invested (INR/8 decimal numeric)
    ``current_value`` — last known market or maturity value

    Transaction history is stored in InvestmentTransaction (child model).
    Portfolio calculations belong to the Financial Engine, not this model.
    """

    __tablename__ = "investments"
    __table_args__ = (
        CheckConstraint("principal >= 0", name="ck_investments_principal_non_negative"),
        CheckConstraint(
            "current_value >= 0", name="ck_investments_current_value_non_negative"
        ),
        CheckConstraint(
            "interest_rate >= 0", name="ck_investments_interest_rate_non_negative"
        ),
        CheckConstraint("quantity >= 0", name="ck_investments_quantity_non_negative"),
        Index("ix_investments_user_id_purchase_date", "user_id", "purchase_date"),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    investment_type: Mapped[InvestmentType] = mapped_column(
        SAEnum(InvestmentType, native_enum=False, validate_strings=True, length=20),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    principal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 8), nullable=True
    )  # shares/units; high precision for fractional holdings
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )  # annual rate, e.g. 0.0750
    investment_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="investments"
    )
    transactions: Mapped[list[InvestmentTransaction]] = relationship(
        "InvestmentTransaction",
        back_populates="investment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Investment id={self.id} user_id={self.user_id} "
            f"type={self.investment_type} name={self.name!r}>"
        )


class InvestmentTransaction(Base):
    """A single activity event against an investment holding.

    Records portfolio activity: buy, sell, dividend receipt, interest
    accrual, SIP contribution, and fund withdrawals.  These records allow
    full portfolio performance history to be reconstructed by the Financial
    Engine.

    Nullable fields — not all transaction types require every field:
    - ``quantity`` / ``price_per_unit`` : not applicable to DIVIDEND, INTEREST
    - ``txn_metadata`` : optional extras (e.g. folio number, broker note)

    Only ``created_at`` is stored — transactions are immutable records;
    ``updated_at`` would imply the transaction itself was revised.

    Cascade: InvestmentTransaction is deleted when its parent Investment is
    deleted (investment records without an investment are meaningless).
    """

    __tablename__ = "investment_transactions"
    __table_args__ = (
        CheckConstraint(
            "amount >= 0", name="ck_investment_transactions_amount_non_negative"
        ),
        CheckConstraint(
            "quantity >= 0", name="ck_investment_transactions_quantity_non_negative"
        ),
        CheckConstraint(
            "price_per_unit >= 0",
            name="ck_investment_transactions_price_per_unit_non_negative",
        ),
        Index(
            "ix_investment_transactions_investment_id_date",
            "investment_id",
            "transaction_date",
        ),
    )

    id: Mapped[int] = pk_column()
    investment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("investments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[InvestmentTransactionType] = mapped_column(
        SAEnum(
            InvestmentTransactionType,
            native_enum=False,
            validate_strings=True,
            length=15,
        ),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    price_per_unit: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    txn_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    investment: Mapped[Investment] = relationship(
        "Investment", back_populates="transactions"
    )

    def __repr__(self) -> str:
        return (
            f"<InvestmentTransaction id={self.id} "
            f"investment_id={self.investment_id} type={self.transaction_type}>"
        )
