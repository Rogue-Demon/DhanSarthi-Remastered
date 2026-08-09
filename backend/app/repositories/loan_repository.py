"""Loan repository for DhanSarthi."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.enums import LoanType, LoanStatus
from app.repositories.base import BaseRepository


class LoanRepository(BaseRepository[Loan]):
    """Repository managing Loan database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Loan, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> Loan | None:
        """Retrieve a Loan record by ID for a specific user."""
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
        loan_type: LoanType | None = None,
        status: LoanStatus | None = None,
    ) -> list[Loan]:
        """List Loan records for a specific user with type and status filtering."""
        stmt = select(self.model).where(self.model.user_id == user_id)

        if loan_type is not None:
            stmt = stmt.where(self.model.loan_type == loan_type)
        if status is not None:
            stmt = stmt.where(self.model.status == status)

        stmt = stmt.order_by(self.model.start_date.desc()).limit(limit).offset(offset)
        return list(self._db.execute(stmt).scalars().all())
