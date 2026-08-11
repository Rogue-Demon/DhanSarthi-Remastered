"""Asset API router for DhanSarthi."""

from __future__ import annotations

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_asset_service, get_current_user_id
from app.models.enums import AssetType
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.schemas.common import PaginatedResponse
from app.services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=PaginatedResponse[AssetResponse])
def list_assets(
    user_id: int = Depends(get_current_user_id),
    service: AssetService = Depends(get_asset_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    asset_type: Optional[AssetType] = Query(default=None),
) -> PaginatedResponse[AssetResponse]:
    """List assets owned by the current user with optional filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_assets(
        user_id,
        limit=page_size,
        offset=offset,
        asset_type=asset_type,
    )
    all_items = service.list_assets(
        user_id,
        limit=10000,
        offset=0,
        asset_type=asset_type,
    )
    total = len(all_items)
    total_pages = max(1, ceil(total / page_size))

    serialized = [AssetResponse.model_validate(item) for item in items]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    data: AssetCreate,
    user_id: int = Depends(get_current_user_id),
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    """Create a new asset record for the current user."""
    from datetime import date as date_cls

    asset = service.create_asset(
        user_id,
        name=data.name,
        asset_type=data.asset_type,
        value=data.current_value,
        valuation_date=data.valuation_date or date_cls.today(),
    )
    return AssetResponse.model_validate(asset)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: int,
    user_id: int = Depends(get_current_user_id),
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    """Retrieve a single asset by ID for the current user."""
    asset = service.get_asset(asset_id, user_id)
    return AssetResponse.model_validate(asset)


@router.patch("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    data: AssetUpdate,
    user_id: int = Depends(get_current_user_id),
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    """Update fields on an existing asset record."""
    update_fields = data.model_dump(exclude_unset=True)
    # Map API field 'current_value' to ORM field 'value'
    if "current_value" in update_fields:
        update_fields["value"] = update_fields.pop("current_value")
    asset = service.update_asset(asset_id, user_id, **update_fields)
    return AssetResponse.model_validate(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    user_id: int = Depends(get_current_user_id),
    service: AssetService = Depends(get_asset_service),
) -> None:
    """Delete an asset record."""
    service.delete_asset(asset_id, user_id)
