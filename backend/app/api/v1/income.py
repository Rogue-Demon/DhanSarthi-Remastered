"""Income API router for DhanSarthi."""

from __future__ import annotations

from datetime import date
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_income_service
from app.models.enums import IncomeFrequency
from app.schemas.common import PaginatedResponse
from app.schemas.income import IncomeCreate, IncomeResponse, IncomeUpdate
from app.services.income_service import IncomeService

router = APIRouter(prefix="/income", tags=["income"])


@router.get("", response_model=PaginatedResponse[IncomeResponse])
def list_incomes(
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    category: Optional[str] = Query(default=None),
    frequency: Optional[IncomeFrequency] = Query(default=None),
) -> PaginatedResponse[IncomeResponse]:
    """List income records for the current user with optional filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_incomes(
        user_id,
        limit=page_size,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        category=category,
        frequency=frequency,
    )
    # Fetch total for pagination
    all_items = service.list_incomes(
        user_id,
        limit=10000,
        offset=0,
        date_from=date_from,
        date_to=date_to,
        category=category,
        frequency=frequency,
    )
    total = len(all_items)
    total_pages = max(1, ceil(total / page_size))

    serialized = [IncomeResponse.model_validate(item) for item in items]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    data: IncomeCreate,
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service),
) -> IncomeResponse:
    """Create a new income record for the current user."""
    income = service.create_income(
        user_id,
        source=data.source,
        amount=data.amount,
        income_date=data.income_date,
        category=data.category,
        currency=data.currency,
        frequency=data.frequency,
        description=data.description,
    )
    return IncomeResponse.model_validate(income)


@router.get("/{income_id}", response_model=IncomeResponse)
def get_income(
    income_id: int,
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service),
) -> IncomeResponse:
    """Retrieve a single income record by ID for the current user."""
    income = service.get_income(income_id, user_id)
    return IncomeResponse.model_validate(income)


@router.patch("/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: int,
    data: IncomeUpdate,
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service),
) -> IncomeResponse:
    """Update fields on an existing income record."""
    update_fields = data.model_dump(exclude_unset=True)
    income = service.update_income(income_id, user_id, **update_fields)
    return IncomeResponse.model_validate(income)


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service),
) -> None:
    """Delete (soft-delete) an income record."""
    service.delete_income(income_id, user_id)
