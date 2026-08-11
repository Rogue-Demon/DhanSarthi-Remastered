"""Liability API router for DhanSarthi."""

from __future__ import annotations

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_liability_service
from app.models.enums import LiabilityType
from app.schemas.common import PaginatedResponse
from app.schemas.liability import (
    LiabilityCreate,
    LiabilityResponse,
    LiabilityUpdate,
)
from app.services.liability_service import LiabilityService

router = APIRouter(prefix="/liabilities", tags=["liabilities"])


@router.get("", response_model=PaginatedResponse[LiabilityResponse])
def list_liabilities(
    user_id: int = Depends(get_current_user_id),
    service: LiabilityService = Depends(get_liability_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    liability_type: Optional[LiabilityType] = Query(default=None),
) -> PaginatedResponse[LiabilityResponse]:
    """List liabilities for the current user with optional filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_liabilities(
        user_id,
        limit=page_size,
        offset=offset,
        liability_type=liability_type,
    )
    all_items = service.list_liabilities(
        user_id,
        limit=10000,
        offset=0,
        liability_type=liability_type,
    )
    total = len(all_items)
    total_pages = max(1, ceil(total / page_size))

    serialized = [LiabilityResponse.model_validate(item) for item in items]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=LiabilityResponse, status_code=status.HTTP_201_CREATED)
def create_liability(
    data: LiabilityCreate,
    user_id: int = Depends(get_current_user_id),
    service: LiabilityService = Depends(get_liability_service),
) -> LiabilityResponse:
    """Create a new liability record for the current user."""
    liability = service.create_liability(
        user_id,
        name=data.name,
        liability_type=data.liability_type,
        outstanding_amount=data.outstanding_balance,
        interest_rate=data.interest_rate_percent,
    )
    return LiabilityResponse.model_validate(liability)


@router.get("/{liability_id}", response_model=LiabilityResponse)
def get_liability(
    liability_id: int,
    user_id: int = Depends(get_current_user_id),
    service: LiabilityService = Depends(get_liability_service),
) -> LiabilityResponse:
    """Retrieve a single liability record by ID for the current user."""
    liability = service.get_liability(liability_id, user_id)
    return LiabilityResponse.model_validate(liability)


@router.patch("/{liability_id}", response_model=LiabilityResponse)
def update_liability(
    liability_id: int,
    data: LiabilityUpdate,
    user_id: int = Depends(get_current_user_id),
    service: LiabilityService = Depends(get_liability_service),
) -> LiabilityResponse:
    """Update fields on an existing liability record."""
    update_fields = data.model_dump(exclude_unset=True)
    # Map API field names to ORM field names
    if "outstanding_balance" in update_fields:
        update_fields["outstanding_amount"] = update_fields.pop("outstanding_balance")
    if "interest_rate_percent" in update_fields:
        update_fields["interest_rate"] = update_fields.pop("interest_rate_percent")
    liability = service.update_liability(liability_id, user_id, **update_fields)
    return LiabilityResponse.model_validate(liability)


@router.delete("/{liability_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_liability(
    liability_id: int,
    user_id: int = Depends(get_current_user_id),
    service: LiabilityService = Depends(get_liability_service),
) -> None:
    """Delete a liability record."""
    service.delete_liability(liability_id, user_id)
