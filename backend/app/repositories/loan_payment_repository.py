"""Loan payment repository for DhanSarthi."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanPayment
from app.repositories.base import BaseRepository


class LoanPaymentRepository(BaseRepository[LoanPayment]):
    """Repository managing LoanPayment database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(LoanPayment, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> LoanPayment | None:
        """Retrieve a LoanPayment by ID, ensuring it belongs to the user's loan."""
        stmt = (
            select(self.model)
            .join(Loan, self.model.loan_id == Loan.id)
            .where(self.model.id == record_id)
            .where(Loan.user_id == user_id)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_loan_for_user(
        self,
        loan_id: int,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LoanPayment]:
        """List all payments for a specific loan, verifying user ownership of the parent loan."""
        stmt = (
            select(self.model)
            .join(Loan, self.model.loan_id == Loan.id)
            .where(self.model.loan_id == loan_id)
            .where(Loan.user_id == user_id)
            .order_by(self.model.payment_date.desc(), self.model.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._db.execute(stmt).scalars().all())
