"""Transaction API router for DhanSarthi."""

from __future__ import annotations

from datetime import date
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_transaction_service
from app.models.enums import TransactionType
from app.schemas.common import PaginatedResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=PaginatedResponse[TransactionResponse])
def list_transactions(
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    category: Optional[str] = Query(default=None),
    transaction_type: Optional[TransactionType] = Query(default=None),
) -> PaginatedResponse[TransactionResponse]:
    """List financial movement transactions for the current user with DB filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_transactions(
        user_id,
        limit=page_size,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    all_items = service.list_transactions(
        user_id,
        limit=10000,
        offset=0,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    total = len(all_items)
    total_pages = max(1, ceil(total / page_size))

    serialized = [TransactionResponse.model_validate(item) for item in items]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Create a new transaction record for the current user."""
    tx = service.create_transaction(
        user_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
        transaction_date=data.transaction_date,
        category=data.category,
        description=data.description,
        source=data.source,
    )
    return TransactionResponse.model_validate(tx)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Retrieve a single transaction by ID for the current user."""
    tx = service.get_transaction(transaction_id, user_id)
    return TransactionResponse.model_validate(tx)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Update fields on an existing transaction record."""
    update_fields = data.model_dump(exclude_unset=True)
    tx = service.update_transaction(transaction_id, user_id, **update_fields)
    return TransactionResponse.model_validate(tx)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    service: TransactionService = Depends(get_transaction_service),
) -> None:
    """Delete (soft-delete) a transaction record."""
    service.delete_transaction(transaction_id, user_id)
