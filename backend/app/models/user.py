"""User model — ownership root for all DhanSarthi financial data."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, pk_column


class User(Base, TimestampMixin):
    """Application user account.

    This is the top-level ownership anchor.  Every financial record in
    DhanSarthi belongs to exactly one User via a foreign key.

    Authentication fields (hashed_password, OAuth tokens, refresh tokens,
    email_verified_at, etc.) will be added in the Authentication phase.
    They are deliberately excluded here to keep this phase clean.

    Cascade behaviour
    -----------------
    profile        : CASCADE DELETE  — profile has no meaning without a user.
    Financial data : NO CASCADE      — financial history must be explicitly
                                       managed before account deletion.

    Future models that will also belong to User:
        Document, Conversation, Message, KnowledgeDocument
    """

    __tablename__ = "users"

    id: Mapped[int] = pk_column()
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------ #
    # Relationships (lazy="select" is the SQLAlchemy default)             #
    # ------------------------------------------------------------------ #

    profile: Mapped[Profile] = relationship(  # type: ignore[name-defined]
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    incomes: Mapped[list[Income]] = relationship(  # type: ignore[name-defined]
        "Income", back_populates="user"
    )
    expenses: Mapped[list[Expense]] = relationship(  # type: ignore[name-defined]
        "Expense", back_populates="user"
    )
    transactions: Mapped[list[Transaction]] = relationship(  # type: ignore[name-defined]
        "Transaction", back_populates="user"
    )
    assets: Mapped[list[Asset]] = relationship(  # type: ignore[name-defined]
        "Asset", back_populates="user"
    )
    liabilities: Mapped[list[Liability]] = relationship(  # type: ignore[name-defined]
        "Liability", back_populates="user"
    )
    investments: Mapped[list[Investment]] = relationship(  # type: ignore[name-defined]
        "Investment", back_populates="user"
    )
    loans: Mapped[list[Loan]] = relationship(  # type: ignore[name-defined]
        "Loan", back_populates="user"
    )
    goals: Mapped[list[Goal]] = relationship(  # type: ignore[name-defined]
        "Goal", back_populates="user"
    )
    budgets: Mapped[list[Budget]] = relationship(  # type: ignore[name-defined]
        "Budget", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
