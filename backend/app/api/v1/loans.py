"""Loan API router for DhanSarthi."""

from __future__ import annotations

from math import ceil
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_loan_service
from app.models.enums import LoanStatus, LoanType
from app.schemas.common import PaginatedResponse
from app.schemas.loan import (
    LoanCreate,
    LoanPaymentCreate,
    LoanPaymentResponse,
    LoanResponse,
    LoanUpdate,
)
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("", response_model=PaginatedResponse[LoanResponse])
def list_loans(
    user_id: int = Depends(get_current_user_id),
    service: LoanService = Depends(get_loan_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    loan_type: Optional[LoanType] = Query(default=None),
    loan_status: Optional[LoanStatus] = Query(default=None, alias="status"),
) -> PaginatedResponse[LoanResponse]:
    """List loans for the current user with optional filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_loans(
        user_id,
        limit=page_size,
        offset=offset,
        loan_type=loan_type,
        status=loan_status,
    )
    all_items = service.list_loans(
        user_id,
        limit=10000,
        offset=0,
        loan_type=loan_type,
        status=loan_status,
    )
    total = len(all_items)
    total_pages = max(1, ceil(total / page_size))

    serialized = [
        LoanResponse(
            id=item.id,
            user_id=item.user_id,
            name=getattr(item, "name", None) or f"{item.loan_type.value if hasattr(item.loan_type, 'value') else item.loan_type} Loan",
            loan_type=item.loan_type,
            principal_amount=item.principal_amount,
            interest_rate_percent=item.interest_rate,
            tenure_months=item.tenure,
            monthly_emi=item.emi or (item.principal_amount / item.tenure),
            start_date=item.start_date,
            end_date=item.end_date,
            lender=item.lender,
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    data: LoanCreate,
    user_id: int = Depends(get_current_user_id),
    service: LoanService = Depends(get_loan_service),
) -> LoanResponse:
    """Create a new loan record for the current user."""
    loan = service.create_loan(
        user_id,
        loan_type=data.loan_type,
        lender=data.lender or "Bank",
        principal_amount=data.principal_amount,
        outstanding_amount=data.principal_amount,
        interest_rate=data.interest_rate_percent,
        tenure=data.tenure_months,
        start_date=data.start_date,
        emi=data.monthly_emi,
        end_date=data.end_date,
        status=data.status,
    )
    return LoanResponse(
        id=loan.id,
        user_id=loan.user_id,
        name=data.name,
        loan_type=loan.loan_type,
        principal_amount=loan.principal_amount,
        interest_rate_percent=loan.interest_rate,
        tenure_months=loan.tenure,
        monthly_emi=loan.emi,
        start_date=loan.start_date,
        end_date=loan.end_date,
        lender=loan.lender,
        status=loan.status,
        created_at=loan.created_at,
        updated_at=loan.updated_at,
    )


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(
    loan_id: int,
    user_id: int = Depends(get_current_user_id),
    service: LoanService = Depends(get_loan_service),
) -> LoanResponse:
    """Retrieve a single loan by ID for the current user."""
    loan = service.get_loan(loan_id, user_id)
    return LoanResponse(
        id=loan.id,
        user_id=loan.user_id,
        name=getattr(loan, "name", None) or f"{loan.loan_type.value if hasattr(loan.loan_type, 'value') else loan.loan_type} Loan",
        loan_type=loan.loan_type,
        principal_amount=loan.principal_amount,
        interest_rate_percent=loan.interest_rate,
        tenure_months=loan.tenure,
        monthly_emi=loan.emi or (loan.principal_amount / loan.tenure),
        start_date=loan.start_date,
        end_date=loan.end_date,
        lender=loan.lender,
        status=loan.status,
        created_at=loan.created_at,
        updated_at=loan.updated_at,
    )


@router.patch("/{loan_id}", response_model=LoanResponse)
def update_loan(
    loan_id: int,
    data: LoanUpdate,
    user_id: int = Depends(get_current_user_id),
    service: LoanService = Depends(get_loan_service),
) -> LoanResponse:
    """Update fields on an existing loan record."""
    update_fields = data.model_dump(exclude_unset=True)
    if "interest_rate_percent" in update_fields:
        update_fields["interest_rate"] = update_fields.pop("interest_rate_percent")
    if "tenure_months" in update_fields:
        update_fields["tenure"] = update_fields.pop("tenure_months")
    if "monthly_emi" in update_fields:
        update_fields["emi"] = update_fields.pop("monthly_emi")

    loan = service.update_loan(loan_id, user_id, **update_fields)
    return LoanResponse(
        id=loan.id,
        user_id=loan.user_id,
        name=data.name or getattr(loan, "name", None) or f"{loan.loan_type.value if hasattr(loan.loan_type, 'value') else loan.loan_type} Loan",
        loan_type=loan.loan_type,
        principal_amount=loan.principal_amount,
        interest_rate_percent=loan.interest_rate,
        tenure_months=loan.tenure,
        monthly_emi=loan.emi,
        start_date=loan.start_date,
        end_date=loan.end_date,
        lender=loan.lender,
        status=loan.status,
        created_at=loan.created_at,
        updated_at=loan.updated_at,
    )


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(
    loan_id: int,
    user_id: int = Depends(get_current_user_id),
    service: LoanService = Depends(get_loan_service),
) -> None:
    """Delete a loan record."""
    service.delete_loan(loan_id, user_id)


# ============================================================================
# Loan Payments (Nested Endpoints)
# ============================================================================


@router.get(
    "/{loan_id}/payments",
    response_model=List[LoanPaymentResponse],
)
def list_loan_payments(
    loan_id: int,
    user_id: int = Depends(get_current_user_id),
    service: LoanService = Depends(get_loan_service),
) -> List[LoanPaymentResponse]:
    """List loan payments for a specific loan owned by the current user."""
    payments = service.list_loan_payments(loan_id, user_id)
    return [LoanPaymentResponse.model_validate(p) for p in payments]


@router.post(
    "/{loan_id}/payments",
    response_model=LoanPaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_loan_payment(
    loan_id: int,
    data: LoanPaymentCreate,
    user_id: int = Depends(get_current_user_id),
    service: LoanService = Depends(get_loan_service),
) -> LoanPaymentResponse:
    """Record a payment for a loan owned by the current user."""
    payment = service.create_loan_payment(
        loan_id,
        user_id,
        payment_date=data.payment_date,
        amount=data.amount,
        principal_component=data.principal_component,
        interest_component=data.interest_component,
    )
    return LoanPaymentResponse.model_validate(payment)


@router.get(
    "/{loan_id}/payments/{payment_id}",
    response_model=LoanPaymentResponse,
)
def get_loan_payment(
    loan_id: int,
    payment_id: int,
    user_id: int = Depends(get_current_user_id),
    service: LoanService = Depends(get_loan_service),
) -> LoanPaymentResponse:
    """Retrieve a single loan payment after verifying ownership."""
    service.get_loan(loan_id, user_id)
    payment = service.get_loan_payment(payment_id, user_id)
    if payment.loan_id != loan_id:
        from app.core.exceptions import ResourceNotFoundError

        raise ResourceNotFoundError(resource="LoanPayment", identifier=payment_id)
    return LoanPaymentResponse.model_validate(payment)
