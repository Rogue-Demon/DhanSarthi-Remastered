"""Budget repository for DhanSarthi."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.enums import BudgetPeriod
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    """Repository managing Budget database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Budget, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> Budget | None:
        """Retrieve a Budget record by ID for a specific user."""
        stmt = (
            select(self.model)
            .where(self.model.id == record_id)
            .where(self.model.user_id == user_id)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        category: str | None = None,
        period: BudgetPeriod | None = None,
        active_on: date | None = None,
    ) -> list[Budget]:
        """List Budget records for a specific user with optional filtering.

        Parameters
        ----------
        category:
            Filter by exact spending category string.
        period:
            Filter by BudgetPeriod (WEEKLY, MONTHLY, YEARLY, CUSTOM).
        active_on:
            Filter budgets whose date range covers this date
            (start_date <= active_on AND (end_date IS NULL OR end_date >= active_on)).
        """
        stmt = select(self.model).where(self.model.user_id == user_id)

        if category is not None:
            stmt = stmt.where(self.model.category == category)
        if period is not None:
            stmt = stmt.where(self.model.period == period)
        if active_on is not None:
            stmt = stmt.where(self.model.start_date <= active_on).where(
                (self.model.end_date.is_(None)) | (self.model.end_date >= active_on)
            )

        stmt = (
            stmt.order_by(self.model.start_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._db.execute(stmt).scalars().all())
