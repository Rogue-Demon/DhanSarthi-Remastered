"""Transaction repository for DhanSarthi."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.enums import TransactionType
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    """Repository managing Transaction database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Transaction, db)

    def get_by_id_for_user(self, record_id: int, user_id: int) -> Transaction | None:
        """Retrieve an active (non-soft-deleted) Transaction record by ID for a specific user."""
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
        transaction_type: TransactionType | None = None,
        category: str | None = None,
        search: str | None = None,
        sort: str = "date_desc",
    ) -> list[Transaction]:
        """List active Transactions for a user with comprehensive filters and sorting."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .where(self.model.deleted_at.is_(None))
        )

        # Filters
        if date_from is not None:
            stmt = stmt.where(self.model.transaction_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(self.model.transaction_date <= date_to)
        if transaction_type is not None:
            stmt = stmt.where(self.model.transaction_type == transaction_type)
        if category is not None:
            stmt = stmt.where(self.model.category == category)
        if search is not None and search.strip():
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    self.model.description.ilike(search_pattern),
                    self.model.source.ilike(search_pattern),
                )
            )

        # Sorting
        if sort == "date_asc":
            stmt = stmt.order_by(self.model.transaction_date.asc(), self.model.id.asc())
        elif sort == "amount_desc":
            stmt = stmt.order_by(self.model.amount.desc(), self.model.id.desc())
        elif sort == "amount_asc":
            stmt = stmt.order_by(self.model.amount.asc(), self.model.id.asc())
        else:  # default date_desc
            stmt = stmt.order_by(self.model.transaction_date.desc(), self.model.id.desc())

        stmt = stmt.limit(limit).offset(offset)
        return list(self._db.execute(stmt).scalars().all())
