"""Expense repository for DhanSarthi."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.enums import ExpenseFrequency
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository[Expense]):
    """Repository managing Expense database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Expense, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> Expense | None:
        """Retrieve an active (non-soft-deleted) Expense record by ID for a specific user."""
        stmt = (
            select(self.model)
            .where(self.model.id == record_id)
            .where(self.model.user_id == user_id)
            .where(self.model.deleted_at.is_(None))
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        date_from: date | None = None,
        date_to: date | None = None,
        category: str | None = None,
        frequency: ExpenseFrequency | None = None,
        amount_min: Decimal | None = None,
        amount_max: Decimal | None = None,
    ) -> list[Expense]:
        """List active (non-soft-deleted) Expense records for a specific user with filters."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.deleted_at.is_(None))
        )

        if date_from is not None:
            stmt = stmt.where(self.model.expense_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(self.model.expense_date <= date_to)
        if category is not None:
            stmt = stmt.where(self.model.category == category)
        if frequency is not None:
            stmt = stmt.where(self.model.frequency == frequency)
        if amount_min is not None:
            stmt = stmt.where(self.model.amount >= amount_min)
        if amount_max is not None:
            stmt = stmt.where(self.model.amount <= amount_max)

        stmt = stmt.order_by(self.model.expense_date.desc()).limit(limit).offset(offset)
        return list(self._db.execute(stmt).scalars().all())
