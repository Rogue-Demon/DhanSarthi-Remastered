"""Transaction service for DhanSarthi."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository


class TransactionService:
    """Coordinates Transaction business logic, ownership isolation, and persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = TransactionRepository(db)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_transaction(self, transaction_id: int, user_id: int) -> Transaction:
        """Retrieve a single transaction record for *user_id*, or raise 404."""
        record = self._repo.get_by_id_for_user(transaction_id, user_id)
        if record is None:
            raise ResourceNotFoundError(
                resource="Transaction", identifier=transaction_id
            )
        return record

    def list_transactions(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        transaction_type: TransactionType | None = None,
        category: str | None = None,
        search: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort: str = "date_desc",
    ) -> list[Transaction]:
        """List transaction records for *user_id* with dashboard-style filtering."""
        return self._repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            transaction_type=transaction_type,
            category=category,
            search=search,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create_transaction(
        self,
        user_id: int,
        *,
        transaction_type: TransactionType,
        amount: Decimal,
        transaction_date: date,
        category: str = "Other",
        currency: str = "INR",
        description: str | None = None,
        source: str | None = None,
    ) -> Transaction:
        """Create a new Transaction record for *user_id*."""
        txn = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            transaction_date=transaction_date,
            category=category,
            currency=currency,
            description=description,
            source=source,
        )
        with handle_db_exceptions(resource="Transaction"):
            self._repo.add(txn)
            self._db.commit()
        self._db.refresh(txn)
        return txn

    def update_transaction(
        self,
        transaction_id: int,
        user_id: int,
        **fields: object,
    ) -> Transaction:
        """Update mutable fields on an existing Transaction record."""
        record = self.get_transaction(transaction_id, user_id)

        allowed = {
            "transaction_type", "amount", "transaction_date", "category",
            "currency", "description", "source",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Transaction"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_transaction(self, transaction_id: int, user_id: int) -> None:
        """Soft-delete a Transaction record by setting deleted_at."""
        record = self.get_transaction(transaction_id, user_id)
        record.deleted_at = datetime.now(timezone.utc)
        with handle_db_exceptions(resource="Transaction"):
            self._db.commit()
