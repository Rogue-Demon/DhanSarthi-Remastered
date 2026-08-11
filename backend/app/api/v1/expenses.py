"""Expense API router for DhanSarthi."""

from __future__ import annotations

from datetime import date
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_expense_service
from app.models.enums import ExpenseFrequency
from app.schemas.common import PaginatedResponse
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=PaginatedResponse[ExpenseResponse])
def list_expenses(
    user_id: int = Depends(get_current_user_id),
    service: ExpenseService = Depends(get_expense_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    category: Optional[str] = Query(default=None),
    frequency: Optional[ExpenseFrequency] = Query(default=None),
) -> PaginatedResponse[ExpenseResponse]:
    """List expense records for the current user with optional filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_expenses(
        user_id,
        limit=page_size,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        category=category,
        frequency=frequency,
    )
    all_items = service.list_expenses(
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

    serialized = [ExpenseResponse.model_validate(item) for item in items]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    user_id: int = Depends(get_current_user_id),
    service: ExpenseService = Depends(get_expense_service),
) -> ExpenseResponse:
    """Create a new expense record for the current user."""
    expense = service.create_expense(
        user_id,
        category=data.category,
        amount=data.amount,
        expense_date=data.expense_date,
        currency=data.currency,
        frequency=data.frequency,
        description=data.description,
    )
    return ExpenseResponse.model_validate(expense)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    user_id: int = Depends(get_current_user_id),
    service: ExpenseService = Depends(get_expense_service),
) -> ExpenseResponse:
    """Retrieve a single expense record by ID for the current user."""
    expense = service.get_expense(expense_id, user_id)
    return ExpenseResponse.model_validate(expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    user_id: int = Depends(get_current_user_id),
    service: ExpenseService = Depends(get_expense_service),
) -> ExpenseResponse:
    """Update fields on an existing expense record."""
    update_fields = data.model_dump(exclude_unset=True)
    expense = service.update_expense(expense_id, user_id, **update_fields)
    return ExpenseResponse.model_validate(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    user_id: int = Depends(get_current_user_id),
    service: ExpenseService = Depends(get_expense_service),
) -> None:
    """Delete (soft-delete) an expense record."""
    service.delete_expense(expense_id, user_id)
