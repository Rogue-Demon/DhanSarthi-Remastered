"""Expense service for DhanSarthi."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import ExpenseFrequency
from app.models.expense import Expense
from app.repositories.expense_repository import ExpenseRepository


class ExpenseService:
    """Coordinates Expense business logic, ownership isolation, and persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = ExpenseRepository(db)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_expense(self, expense_id: int, user_id: int) -> Expense:
        """Retrieve a single expense record for *user_id*, or raise 404."""
        record = self._repo.get_by_id_for_user(expense_id, user_id)
        if record is None:
            raise ResourceNotFoundError(resource="Expense", identifier=expense_id)
        return record

    def list_expenses(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        date_from: date | None = None,
        date_to: date | None = None,
        category: str | None = None,
        frequency: ExpenseFrequency | None = None,
    ) -> list[Expense]:
        """List expense records for *user_id* with optional filters."""
        return self._repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            date_from=date_from,
            date_to=date_to,
            category=category,
            frequency=frequency,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create_expense(
        self,
        user_id: int,
        *,
        category: str,
        amount: Decimal,
        expense_date: date,
        currency: str = "INR",
        description: str | None = None,
        frequency: ExpenseFrequency | None = None,
    ) -> Expense:
        """Create a new Expense record for *user_id*."""
        expense = Expense(
            user_id=user_id,
            category=category,
            amount=amount,
            expense_date=expense_date,
            currency=currency,
            description=description,
            frequency=frequency,
        )
        with handle_db_exceptions(resource="Expense"):
            self._repo.add(expense)
            self._db.commit()
        self._db.refresh(expense)
        return expense

    def update_expense(
        self,
        expense_id: int,
        user_id: int,
        **fields: object,
    ) -> Expense:
        """Update mutable fields on an existing Expense record."""
        record = self.get_expense(expense_id, user_id)

        allowed = {
            "category", "amount", "expense_date", "currency",
            "description", "frequency",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Expense"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_expense(self, expense_id: int, user_id: int) -> None:
        """Soft-delete an Expense record by setting deleted_at."""
        record = self.get_expense(expense_id, user_id)
        record.deleted_at = datetime.now(timezone.utc)
        with handle_db_exceptions(resource="Expense"):
            self._db.commit()
