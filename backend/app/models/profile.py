"""Profile model — one-to-one with User, holds persona and preferences."""

from __future__ import annotations

from sqlalchemy import BigInteger, Enum as SAEnum, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Persona, RiskProfile
from app.models.mixins import TimestampMixin, pk_column


class Profile(Base, TimestampMixin):
    """User financial profile — persona and preference data.

    Holds the DhanSarthi persona (STUDENT / PROFESSIONAL / BUSINESS) that
    determines which dashboard layout and feature set is shown to the user.

    The ``UNIQUE(user_id)`` constraint enforces the one-to-one relationship
    at the database level in addition to the application-level relationship.

    ``financial_preferences`` stores flexible per-user settings as JSON
    (e.g. preferred investment categories, dashboard widget order, currency
    display format).  It is intentionally not split into dedicated columns
    because these preferences are UI-configuration data, not financial facts.

    ``country``  — ISO 3166-1 alpha-3 (e.g. "IND")
    ``currency`` — ISO 4217 code (e.g. "INR")
    """

    __tablename__ = "profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_profiles_user_id"),
    )

    id: Mapped[int] = pk_column()
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    persona: Mapped[Persona] = mapped_column(
        SAEnum(Persona, native_enum=False, validate_strings=True, length=20),
        nullable=False,
    )
    country: Mapped[str] = mapped_column(String(3), nullable=False, default="IND")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    risk_profile: Mapped[RiskProfile | None] = mapped_column(
        SAEnum(RiskProfile, native_enum=False, validate_strings=True, length=15),
        nullable=True,
    )
    financial_preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped[User] = relationship(  # type: ignore[name-defined]
        "User", back_populates="profile"
    )

    def __repr__(self) -> str:
        return f"<Profile user_id={self.user_id} persona={self.persona}>"
