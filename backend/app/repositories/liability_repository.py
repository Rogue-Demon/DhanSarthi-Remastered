"""Liability repository for DhanSarthi."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.liability import Liability
from app.models.enums import LiabilityType
from app.repositories.base import BaseRepository


class LiabilityRepository(BaseRepository[Liability]):
    """Repository managing Liability database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Liability, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> Liability | None:
        """Retrieve a Liability record by ID for a specific user."""
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
        liability_type: LiabilityType | None = None,
    ) -> list[Liability]:
        """List Liability records for a specific user with type filtering."""
        stmt = select(self.model).where(self.model.user_id == user_id)

        if liability_type is not None:
            stmt = stmt.where(self.model.liability_type == liability_type)

        stmt = stmt.order_by(self.model.name.asc()).limit(limit).offset(offset)
        return list(self._db.execute(stmt).scalars().all())
