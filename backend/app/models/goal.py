"""Goal model — user financial targets."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, Enum as SAEnum, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import GoalStatus
from app.models.mixins import TimestampMixin, pk_column


class Goal(Base, TimestampMixin):
    """A user financial goal with a target amount and deadline.

    Examples: Emergency Fund, Education, Travel, Home Purchase,
    Retirement, Business Expansion.

    ``priority`` — integer 1 (highest) to 5 (lowest) allowing the user
    to order multiple active goals.

    ``current_amount`` — how much has been set aside toward this goal.
    Starts at 0 and is updated as the user tracks progress.

    Goal projections (required contribution, projected completion date,
    shortfall analysis) belong to the Financial Engine and are not
    computed in this model.
    """

    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="ck_goals_target_amount_positive"),
        CheckConstraint(
            "current_amount >= 0", name="ck_goals_current_amount_non_negative"
        ),
        CheckConstraint(
            "priority BETWEEN 1 AND 5", name="ck_goals_priority_range"
        ),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=3
    )  # 1 = highest, 5 = lowest
    status: Mapped[GoalStatus] = mapped_column(
        SAEnum(GoalStatus, native_enum=False, validate_strings=True, length=15),
        nullable=False,
        default=GoalStatus.ACTIVE,
    )

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="goals"
    )

    def __repr__(self) -> str:
        return (
            f"<Goal id={self.id} user_id={self.user_id} "
            f"name={self.name!r} status={self.status}>"
        )
