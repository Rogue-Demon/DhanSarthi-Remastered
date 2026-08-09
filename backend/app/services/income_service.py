"""Income service for DhanSarthi."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import IncomeFrequency
from app.models.income import Income
from app.repositories.income_repository import IncomeRepository


class IncomeService:
    """Coordinates Income business logic, ownership isolation, and persistence.

    Transaction boundary: each public method commits on success;
    ``handle_db_exceptions`` translates SQLAlchemy errors into application
    exceptions.  No financial calculations are performed here.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = IncomeRepository(db)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_income(self, income_id: int, user_id: int) -> Income:
        """Retrieve a single income record for *user_id*, or raise 404."""
        record = self._repo.get_by_id_for_user(income_id, user_id)
        if record is None:
            raise ResourceNotFoundError(resource="Income", identifier=income_id)
        return record

    def list_incomes(
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
        """List income records for *user_id* with optional filters."""
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

    def create_income(
        self,
        user_id: int,
        *,
        source: str,
        amount: Decimal,
        income_date: date,
        category: str = "Other",
        currency: str = "INR",
        frequency: IncomeFrequency = IncomeFrequency.ONE_TIME,
        description: str | None = None,
    ) -> Income:
        """Create a new Income record for *user_id*."""
        income = Income(
            user_id=user_id,
            source=source,
            amount=amount,
            income_date=income_date,
            category=category,
            currency=currency,
            frequency=frequency,
            description=description,
        )
        with handle_db_exceptions(resource="Income"):
            self._repo.add(income)
            self._db.commit()
        self._db.refresh(income)
        return income

    def update_income(
        self,
        income_id: int,
        user_id: int,
        **fields: object,
    ) -> Income:
        """Update mutable fields on an existing Income record.

        Only fields present in *fields* are updated; unknown keys are ignored.
        """
        record = self.get_income(income_id, user_id)

        allowed = {
            "source", "amount", "income_date", "category",
            "currency", "frequency", "description",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Income"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_income(self, income_id: int, user_id: int) -> None:
        """Soft-delete an Income record by setting deleted_at."""
        from datetime import datetime, timezone

        record = self.get_income(income_id, user_id)
        record.deleted_at = datetime.now(timezone.utc)
        with handle_db_exceptions(resource="Income"):
            self._db.commit()
