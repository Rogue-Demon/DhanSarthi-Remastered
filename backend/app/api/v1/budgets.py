"""Budget API router for DhanSarthi."""

from __future__ import annotations

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_budget_service, get_current_user_id
from app.models.enums import BudgetPeriod
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate
from app.schemas.common import PaginatedResponse
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=PaginatedResponse[BudgetResponse])
def list_budgets(
    user_id: int = Depends(get_current_user_id),
    service: BudgetService = Depends(get_budget_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(default=None),
    period: Optional[BudgetPeriod] = Query(default=None),
) -> PaginatedResponse[BudgetResponse]:
    """List budgets set by the current user with optional filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_budgets(
        user_id,
        limit=page_size,
        offset=offset,
        category=category,
        period=period,
    )
    all_items = service.list_budgets(
        user_id,
        limit=10000,
        offset=0,
        category=category,
        period=period,
    )
    total = len(all_items)
    total_pages = max(1, ceil(total / page_size))

    serialized = [BudgetResponse.model_validate(item) for item in items]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    user_id: int = Depends(get_current_user_id),
    service: BudgetService = Depends(get_budget_service),
) -> BudgetResponse:
    """Create a new budget record for the current user."""
    budget = service.create_budget(
        user_id,
        category=data.category,
        amount=data.amount,
        period=data.period,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    return BudgetResponse.model_validate(budget)


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    user_id: int = Depends(get_current_user_id),
    service: BudgetService = Depends(get_budget_service),
) -> BudgetResponse:
    """Retrieve a single budget record by ID for the current user."""
    budget = service.get_budget(budget_id, user_id)
    return BudgetResponse.model_validate(budget)


@router.patch("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    user_id: int = Depends(get_current_user_id),
    service: BudgetService = Depends(get_budget_service),
) -> BudgetResponse:
    """Update fields on an existing budget record."""
    update_fields = data.model_dump(exclude_unset=True)
    budget = service.update_budget(budget_id, user_id, **update_fields)
    return BudgetResponse.model_validate(budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    user_id: int = Depends(get_current_user_id),
    service: BudgetService = Depends(get_budget_service),
) -> None:
    """Delete a budget record."""
    service.delete_budget(budget_id, user_id)
