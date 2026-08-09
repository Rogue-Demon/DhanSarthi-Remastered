"""Investment repository for DhanSarthi."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.investment import Investment
from app.models.enums import InvestmentType
from app.repositories.base import BaseRepository


class InvestmentRepository(BaseRepository[Investment]):
    """Repository managing Investment database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Investment, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> Investment | None:
        """Retrieve an Investment record by ID for a specific user."""
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
        investment_type: InvestmentType | None = None,
    ) -> list[Investment]:
        """List Investment records for a specific user with type filtering."""
        stmt = select(self.model).where(self.model.user_id == user_id)

        if investment_type is not None:
            stmt = stmt.where(self.model.investment_type == investment_type)

        stmt = stmt.order_by(self.model.purchase_date.desc()).limit(limit).offset(offset)
        return list(self._db.execute(stmt).scalars().all())
