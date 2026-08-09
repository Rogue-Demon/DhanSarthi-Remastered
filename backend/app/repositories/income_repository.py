"""Income repository for DhanSarthi."""

from __future__ import annotations

from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.income import Income
from app.models.enums import IncomeFrequency
from app.repositories.base import BaseRepository


class IncomeRepository(BaseRepository[Income]):
    """Repository managing Income database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Income, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> Income | None:
        """Retrieve an active (non-soft-deleted) Income record by ID for a specific user."""
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
        frequency: IncomeFrequency | None = None,
    ) -> list[Income]:
        """List active (non-soft-deleted) Income records for a specific user with filters."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.deleted_at.is_(None))
        )

        if date_from is not None:
            stmt = stmt.where(self.model.income_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(self.model.income_date <= date_to)
        if category is not None:
            stmt = stmt.where(self.model.category == category)
        if frequency is not None:
            stmt = stmt.where(self.model.frequency == frequency)

        stmt = stmt.order_by(self.model.income_date.desc()).limit(limit).offset(offset)
        return list(self._db.execute(stmt).scalars().all())
