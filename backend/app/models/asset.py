"""Asset model — user-owned assets for net worth calculation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, Enum as SAEnum, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AssetType
from app.models.mixins import TimestampMixin, pk_column


class Asset(Base, TimestampMixin):
    """A user-owned asset contributing to net worth.

    Covers cash, bank balances, property, gold, and other assets.
    Investment holdings are tracked separately in the Investment model to
    support portfolio-level analysis.

    ``valuation_date`` records when the value was last assessed — important
    for assets whose market value changes over time (property, gold).

    ``asset_metadata`` (stored as the column name ``metadata``) captures
    type-specific details without polluting the schema with sparse columns:
    - PROPERTY: {"address": "...", "area_sqft": 1200}
    - GOLD: {"weight_grams": 50, "purity": "22K"}
    - BANK_BALANCE: {"bank_name": "HDFC", "account_last4": "4321"}

    Note: the Python attribute is ``asset_metadata`` to avoid shadowing
    SQLAlchemy's internal ``metadata`` attribute on model instances.
    """

    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint("value >= 0", name="ck_assets_value_non_negative"),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, native_enum=False, validate_strings=True, length=20),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    asset_metadata: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="assets"
    )

    def __repr__(self) -> str:
        return (
            f"<Asset id={self.id} user_id={self.user_id} "
            f"type={self.asset_type} name={self.name!r} value={self.value}>"
        )
