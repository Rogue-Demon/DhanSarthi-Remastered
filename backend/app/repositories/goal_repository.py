"""Goal repository for DhanSarthi."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import GoalStatus
from app.models.goal import Goal
from app.repositories.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    """Repository managing Goal database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Goal, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> Goal | None:
        """Retrieve a Goal record by ID for a specific user."""
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
        status: GoalStatus | None = None,
        priority: int | None = None,
        target_date_before: date | None = None,
        target_date_after: date | None = None,
    ) -> list[Goal]:
        """List Goal records for a specific user with optional filtering.

        Parameters
        ----------
        status:
            Filter by GoalStatus (ACTIVE, COMPLETED, PAUSED, CANCELLED).
        priority:
            Filter by exact priority value (1-5).
        target_date_before:
            Include goals with target_date on or before this date.
        target_date_after:
            Include goals with target_date on or after this date.
        """
        stmt = select(self.model).where(self.model.user_id == user_id)

        if status is not None:
            stmt = stmt.where(self.model.status == status)
        if priority is not None:
            stmt = stmt.where(self.model.priority == priority)
        if target_date_before is not None:
            stmt = stmt.where(self.model.target_date <= target_date_before)
        if target_date_after is not None:
            stmt = stmt.where(self.model.target_date >= target_date_after)

        stmt = (
            stmt.order_by(self.model.priority.asc(), self.model.target_date.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._db.execute(stmt).scalars().all())
