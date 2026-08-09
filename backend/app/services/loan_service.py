"""Loan service for DhanSarthi."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import LoanStatus, LoanType
from app.models.loan import Loan, LoanPayment
from app.repositories.loan_repository import LoanRepository
from app.repositories.loan_payment_repository import LoanPaymentRepository


class LoanService:
    """Coordinates Loan and LoanPayment business logic.

    Ownership is always verified through user_id — the loan_payment
    repository joins back to the parent Loan to enforce this.

    No EMI calculations, amortization schedules, or affordability analysis
    are performed here — those belong to the Financial Engine.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._loan_repo = LoanRepository(db)
        self._payment_repo = LoanPaymentRepository(db)

    # ==================================================================
    # Loans
    # ==================================================================

    def get_loan(self, loan_id: int, user_id: int) -> Loan:
        """Retrieve a single loan for *user_id*, or raise 404."""
        record = self._loan_repo.get_by_id_for_user(loan_id, user_id)
        if record is None:
            raise ResourceNotFoundError(resource="Loan", identifier=loan_id)
        return record

    def list_loans(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        loan_type: LoanType | None = None,
        status: LoanStatus | None = None,
    ) -> list[Loan]:
        """List loan records for *user_id* with optional type and status filters."""
        return self._loan_repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            loan_type=loan_type,
            status=status,
        )

    def create_loan(
        self,
        user_id: int,
        *,
        loan_type: LoanType,
        lender: str,
        principal_amount: Decimal,
        outstanding_amount: Decimal,
        interest_rate: Decimal,
        tenure: int,
        start_date: date,
        currency: str = "INR",
        remaining_tenure: int | None = None,
        emi: Decimal | None = None,
        end_date: date | None = None,
        status: LoanStatus = LoanStatus.ACTIVE,
    ) -> Loan:
        """Create a new Loan record for *user_id*."""
        loan = Loan(
            user_id=user_id,
            loan_type=loan_type,
            lender=lender,
            principal_amount=principal_amount,
            outstanding_amount=outstanding_amount,
            interest_rate=interest_rate,
            tenure=tenure,
            start_date=start_date,
            currency=currency,
            remaining_tenure=remaining_tenure,
            emi=emi,
            end_date=end_date,
            status=status,
        )
        with handle_db_exceptions(resource="Loan"):
            self._loan_repo.add(loan)
            self._db.commit()
        self._db.refresh(loan)
        return loan

    def update_loan(
        self,
        loan_id: int,
        user_id: int,
        **fields: object,
    ) -> Loan:
        """Update mutable fields on an existing Loan record."""
        record = self.get_loan(loan_id, user_id)

        allowed = {
            "loan_type", "lender", "principal_amount", "outstanding_amount",
            "currency", "interest_rate", "tenure", "remaining_tenure",
            "emi", "start_date", "end_date", "status",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Loan"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_loan(self, loan_id: int, user_id: int) -> None:
        """Hard-delete a Loan and its child payments (CASCADE)."""
        record = self.get_loan(loan_id, user_id)
        with handle_db_exceptions(resource="Loan"):
            self._loan_repo.delete(record)
            self._db.commit()

    # ==================================================================
    # Loan Payments
    # ==================================================================

    def get_loan_payment(self, payment_id: int, user_id: int) -> LoanPayment:
        """Retrieve a single loan payment, verifying parent loan ownership."""
        record = self._payment_repo.get_by_id_for_user(payment_id, user_id)
        if record is None:
            raise ResourceNotFoundError(
                resource="LoanPayment", identifier=payment_id
            )
        return record

    def list_loan_payments(
        self,
        loan_id: int,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LoanPayment]:
        """List payments for a specific loan, verifying user ownership."""
        # Ensure the parent loan belongs to this user first.
        self.get_loan(loan_id, user_id)
        return self._payment_repo.list_by_loan_for_user(
            loan_id, user_id, limit=limit, offset=offset
        )

    def create_loan_payment(
        self,
        loan_id: int,
        user_id: int,
        *,
        payment_date: date,
        amount: Decimal,
        principal_component: Decimal | None = None,
        interest_component: Decimal | None = None,
        remaining_balance: Decimal | None = None,
    ) -> LoanPayment:
        """Create a LoanPayment, verifying parent loan ownership."""
        # Ensure the parent loan belongs to this user.
        self.get_loan(loan_id, user_id)

        payment = LoanPayment(
            loan_id=loan_id,
            payment_date=payment_date,
            amount=amount,
            principal_component=principal_component,
            interest_component=interest_component,
            remaining_balance=remaining_balance,
        )
        with handle_db_exceptions(resource="LoanPayment"):
            self._payment_repo.add(payment)
            self._db.commit()
        self._db.refresh(payment)
        return payment
