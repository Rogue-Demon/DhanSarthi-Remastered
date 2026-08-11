"""Investment API router for DhanSarthi."""

from __future__ import annotations

from math import ceil
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_investment_service
from app.models.enums import InvestmentType
from app.schemas.common import PaginatedResponse
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentResponse,
    InvestmentTransactionCreate,
    InvestmentTransactionResponse,
    InvestmentUpdate,
)
from app.services.investment_service import InvestmentService

router = APIRouter(prefix="/investments", tags=["investments"])


@router.get("", response_model=PaginatedResponse[InvestmentResponse])
def list_investments(
    user_id: int = Depends(get_current_user_id),
    service: InvestmentService = Depends(get_investment_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    investment_type: Optional[InvestmentType] = Query(default=None),
) -> PaginatedResponse[InvestmentResponse]:
    """List investment holdings for the current user with optional filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_investments(
        user_id,
        limit=page_size,
        offset=offset,
        investment_type=investment_type,
    )
    all_items = service.list_investments(
        user_id,
        limit=10000,
        offset=0,
        investment_type=investment_type,
    )
    total = len(all_items)
    total_pages = max(1, ceil(total / page_size))

    serialized = [InvestmentResponse.model_validate(item) for item in items]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
def create_investment(
    data: InvestmentCreate,
    user_id: int = Depends(get_current_user_id),
    service: InvestmentService = Depends(get_investment_service),
) -> InvestmentResponse:
    """Create a new investment record for the current user."""
    from datetime import date as date_cls

    purchase_date = data.purchase_date if data.purchase_date else date_cls.today()

    investment = service.create_investment(
        user_id,
        name=data.name,
        investment_type=data.investment_type,
        principal=data.invested_amount,
        current_value=data.current_value,
        purchase_date=purchase_date,
        quantity=data.units,
    )
    return InvestmentResponse.model_validate(investment)


@router.get("/{investment_id}", response_model=InvestmentResponse)
def get_investment(
    investment_id: int,
    user_id: int = Depends(get_current_user_id),
    service: InvestmentService = Depends(get_investment_service),
) -> InvestmentResponse:
    """Retrieve a single investment by ID for the current user."""
    investment = service.get_investment(investment_id, user_id)
    return InvestmentResponse.model_validate(investment)


@router.patch("/{investment_id}", response_model=InvestmentResponse)
def update_investment(
    investment_id: int,
    data: InvestmentUpdate,
    user_id: int = Depends(get_current_user_id),
    service: InvestmentService = Depends(get_investment_service),
) -> InvestmentResponse:
    """Update fields on an existing investment record."""
    update_fields = data.model_dump(exclude_unset=True)
    if "invested_amount" in update_fields:
        update_fields["principal"] = update_fields.pop("invested_amount")
    if "units" in update_fields:
        update_fields["quantity"] = update_fields.pop("units")

    investment = service.update_investment(investment_id, user_id, **update_fields)
    return InvestmentResponse.model_validate(investment)


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
    investment_id: int,
    user_id: int = Depends(get_current_user_id),
    service: InvestmentService = Depends(get_investment_service),
) -> None:
    """Delete an investment record."""
    service.delete_investment(investment_id, user_id)


# ============================================================================
# Investment Transactions (Nested Endpoints)
# ============================================================================


@router.get(
    "/{investment_id}/transactions",
    response_model=List[InvestmentTransactionResponse],
)
def list_investment_transactions(
    investment_id: int,
    user_id: int = Depends(get_current_user_id),
    service: InvestmentService = Depends(get_investment_service),
) -> List[InvestmentTransactionResponse]:
    """List transactions for an investment owned by the current user."""
    txns = service.list_investment_transactions(investment_id, user_id)
    return [InvestmentTransactionResponse.model_validate(t) for t in txns]


@router.post(
    "/{investment_id}/transactions",
    response_model=InvestmentTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_investment_transaction(
    investment_id: int,
    data: InvestmentTransactionCreate,
    user_id: int = Depends(get_current_user_id),
    service: InvestmentService = Depends(get_investment_service),
) -> InvestmentTransactionResponse:
    """Record a transaction against an investment owned by the current user."""
    txn = service.create_investment_transaction(
        investment_id,
        user_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
        transaction_date=data.transaction_date,
        quantity=data.units,
        price_per_unit=data.price_per_unit,
    )
    return InvestmentTransactionResponse.model_validate(txn)


@router.get(
    "/{investment_id}/transactions/{transaction_id}",
    response_model=InvestmentTransactionResponse,
)
def get_investment_transaction(
    investment_id: int,
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    service: InvestmentService = Depends(get_investment_service),
) -> InvestmentTransactionResponse:
    """Retrieve a single investment transaction by ID after ownership verification."""
    service.get_investment(investment_id, user_id)
    txn = service.get_investment_transaction(transaction_id, user_id)
    if txn.investment_id != investment_id:
        from app.core.exceptions import ResourceNotFoundError

        raise ResourceNotFoundError(
            resource="InvestmentTransaction", identifier=transaction_id
        )
    return InvestmentTransactionResponse.model_validate(txn)
