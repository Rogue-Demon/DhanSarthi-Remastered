"""Investment transaction repository for DhanSarthi."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.investment import Investment, InvestmentTransaction
from app.repositories.base import BaseRepository


class InvestmentTransactionRepository(BaseRepository[InvestmentTransaction]):
    """Repository managing InvestmentTransaction database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(InvestmentTransaction, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> InvestmentTransaction | None:
        """Retrieve an InvestmentTransaction by ID, ensuring it belongs to the user's investment."""
        stmt = (
            select(self.model)
            .join(Investment, self.model.investment_id == Investment.id)
            .where(self.model.id == record_id)
            .where(Investment.user_id == user_id)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_investment_for_user(
        self,
        investment_id: int,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InvestmentTransaction]:
        """List all transactions for a specific investment, verifying user ownership of the parent investment."""
        stmt = (
            select(self.model)
            .join(Investment, self.model.investment_id == Investment.id)
            .where(self.model.investment_id == investment_id)
            .where(Investment.user_id == user_id)
            .order_by(self.model.transaction_date.desc(), self.model.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._db.execute(stmt).scalars().all())
