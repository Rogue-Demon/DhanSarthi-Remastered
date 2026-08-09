"""Liability service for DhanSarthi."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import LiabilityType
from app.models.liability import Liability
from app.repositories.liability_repository import LiabilityRepository


class LiabilityService:
    """Coordinates Liability business logic, ownership isolation, and persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = LiabilityRepository(db)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_liability(self, liability_id: int, user_id: int) -> Liability:
        """Retrieve a single liability record for *user_id*, or raise 404."""
        record = self._repo.get_by_id_for_user(liability_id, user_id)
        if record is None:
            raise ResourceNotFoundError(resource="Liability", identifier=liability_id)
        return record

    def list_liabilities(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        liability_type: LiabilityType | None = None,
    ) -> list[Liability]:
        """List liability records for *user_id* with optional type filter."""
        return self._repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            liability_type=liability_type,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create_liability(
        self,
        user_id: int,
        *,
        liability_type: LiabilityType,
        name: str,
        outstanding_amount: Decimal,
        currency: str = "INR",
        interest_rate: Decimal | None = None,
        liability_metadata: dict | None = None,
    ) -> Liability:
        """Create a new Liability record for *user_id*."""
        liability = Liability(
            user_id=user_id,
            liability_type=liability_type,
            name=name,
            outstanding_amount=outstanding_amount,
            currency=currency,
            interest_rate=interest_rate,
            liability_metadata=liability_metadata,
        )
        with handle_db_exceptions(resource="Liability"):
            self._repo.add(liability)
            self._db.commit()
        self._db.refresh(liability)
        return liability

    def update_liability(
        self,
        liability_id: int,
        user_id: int,
        **fields: object,
    ) -> Liability:
        """Update mutable fields on an existing Liability record."""
        record = self.get_liability(liability_id, user_id)

        allowed = {
            "liability_type", "name", "outstanding_amount", "currency",
            "interest_rate", "liability_metadata",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Liability"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_liability(self, liability_id: int, user_id: int) -> None:
        """Hard-delete a Liability record (no soft-delete on this model)."""
        record = self.get_liability(liability_id, user_id)
        with handle_db_exceptions(resource="Liability"):
            self._repo.delete(record)
            self._db.commit()
