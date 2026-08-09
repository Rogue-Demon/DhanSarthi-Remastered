"""Asset service for DhanSarthi."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.asset import Asset
from app.models.enums import AssetType
from app.repositories.asset_repository import AssetRepository


class AssetService:
    """Coordinates Asset business logic, ownership isolation, and persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = AssetRepository(db)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_asset(self, asset_id: int, user_id: int) -> Asset:
        """Retrieve a single asset record for *user_id*, or raise 404."""
        record = self._repo.get_by_id_for_user(asset_id, user_id)
        if record is None:
            raise ResourceNotFoundError(resource="Asset", identifier=asset_id)
        return record

    def list_assets(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        asset_type: AssetType | None = None,
    ) -> list[Asset]:
        """List asset records for *user_id* with optional type filter."""
        return self._repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            asset_type=asset_type,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create_asset(
        self,
        user_id: int,
        *,
        asset_type: AssetType,
        name: str,
        value: Decimal,
        currency: str = "INR",
        valuation_date: date | None = None,
        asset_metadata: dict | None = None,
    ) -> Asset:
        """Create a new Asset record for *user_id*."""
        asset = Asset(
            user_id=user_id,
            asset_type=asset_type,
            name=name,
            value=value,
            currency=currency,
            valuation_date=valuation_date,
            asset_metadata=asset_metadata,
        )
        with handle_db_exceptions(resource="Asset"):
            self._repo.add(asset)
            self._db.commit()
        self._db.refresh(asset)
        return asset

    def update_asset(
        self,
        asset_id: int,
        user_id: int,
        **fields: object,
    ) -> Asset:
        """Update mutable fields on an existing Asset record."""
        record = self.get_asset(asset_id, user_id)

        allowed = {
            "asset_type", "name", "value", "currency",
            "valuation_date", "asset_metadata",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Asset"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_asset(self, asset_id: int, user_id: int) -> None:
        """Hard-delete an Asset record (assets have no soft-delete)."""
        record = self.get_asset(asset_id, user_id)
        with handle_db_exceptions(resource="Asset"):
            self._repo.delete(record)
            self._db.commit()
