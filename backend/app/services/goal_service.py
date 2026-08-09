"""Goal service for DhanSarthi."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import GoalStatus
from app.models.goal import Goal
from app.repositories.goal_repository import GoalRepository


class GoalService:
    """Coordinates Goal business logic, ownership isolation, and persistence.

    No goal projections (required contribution, projected completion date,
    shortfall analysis) are performed here — those belong to the Financial
    Engine.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = GoalRepository(db)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_goal(self, goal_id: int, user_id: int) -> Goal:
        """Retrieve a single goal for *user_id*, or raise 404."""
        record = self._repo.get_by_id_for_user(goal_id, user_id)
        if record is None:
            raise ResourceNotFoundError(resource="Goal", identifier=goal_id)
        return record

    def list_goals(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        status: GoalStatus | None = None,
        priority: int | None = None,
        target_date_before: date | None = None,
        target_date_after: date | None = None,
    ) -> list[Goal]:
        """List goal records for *user_id* with optional filters."""
        return self._repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            status=status,
            priority=priority,
            target_date_before=target_date_before,
            target_date_after=target_date_after,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create_goal(
        self,
        user_id: int,
        *,
        name: str,
        target_amount: Decimal,
        currency: str = "INR",
        current_amount: Decimal = Decimal("0.00"),
        target_date: date | None = None,
        priority: int = 3,
        status: GoalStatus = GoalStatus.ACTIVE,
    ) -> Goal:
        """Create a new Goal record for *user_id*."""
        goal = Goal(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
            currency=currency,
            target_date=target_date,
            priority=priority,
            status=status,
        )
        with handle_db_exceptions(resource="Goal"):
            self._repo.add(goal)
            self._db.commit()
        self._db.refresh(goal)
        return goal

    def update_goal(
        self,
        goal_id: int,
        user_id: int,
        **fields: object,
    ) -> Goal:
        """Update mutable fields on an existing Goal record."""
        record = self.get_goal(goal_id, user_id)

        allowed = {
            "name", "target_amount", "current_amount", "currency",
            "target_date", "priority", "status",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Goal"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_goal(self, goal_id: int, user_id: int) -> None:
        """Hard-delete a Goal record."""
        record = self.get_goal(goal_id, user_id)
        with handle_db_exceptions(resource="Goal"):
            self._repo.delete(record)
            self._db.commit()
