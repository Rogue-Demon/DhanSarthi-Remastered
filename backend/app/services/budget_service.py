"""Budget service for DhanSarthi."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.budget import Budget
from app.models.enums import BudgetPeriod
from app.repositories.budget_repository import BudgetRepository


class BudgetService:
    """Coordinates Budget business logic, ownership isolation, and persistence.

    Budget-vs-actual spending analysis belongs to the Financial Engine and
    is not performed here.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = BudgetRepository(db)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_budget(self, budget_id: int, user_id: int) -> Budget:
        """Retrieve a single budget for *user_id*, or raise 404."""
        record = self._repo.get_by_id_for_user(budget_id, user_id)
        if record is None:
            raise ResourceNotFoundError(resource="Budget", identifier=budget_id)
        return record

    def list_budgets(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        category: str | None = None,
        period: BudgetPeriod | None = None,
        active_on: date | None = None,
    ) -> list[Budget]:
        """List budget records for *user_id* with optional filters."""
        return self._repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            category=category,
            period=period,
            active_on=active_on,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create_budget(
        self,
        user_id: int,
        *,
        category: str,
        amount: Decimal,
        period: BudgetPeriod,
        start_date: date,
        currency: str = "INR",
        end_date: date | None = None,
    ) -> Budget:
        """Create a new Budget record for *user_id*."""
        budget = Budget(
            user_id=user_id,
            category=category,
            amount=amount,
            period=period,
            start_date=start_date,
            currency=currency,
            end_date=end_date,
        )
        with handle_db_exceptions(resource="Budget"):
            self._repo.add(budget)
            self._db.commit()
        self._db.refresh(budget)
        return budget

    def update_budget(
        self,
        budget_id: int,
        user_id: int,
        **fields: object,
    ) -> Budget:
        """Update mutable fields on an existing Budget record."""
        record = self.get_budget(budget_id, user_id)

        allowed = {
            "category", "amount", "currency", "period",
            "start_date", "end_date",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Budget"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_budget(self, budget_id: int, user_id: int) -> None:
        """Hard-delete a Budget record."""
        record = self.get_budget(budget_id, user_id)
        with handle_db_exceptions(resource="Budget"):
            self._repo.delete(record)
            self._db.commit()
