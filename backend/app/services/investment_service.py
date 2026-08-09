"""Investment service for DhanSarthi."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import InvestmentTransactionType, InvestmentType
from app.models.investment import Investment, InvestmentTransaction
from app.repositories.investment_repository import InvestmentRepository
from app.repositories.investment_transaction_repository import InvestmentTransactionRepository


class InvestmentService:
    """Coordinates Investment and InvestmentTransaction business logic.

    Ownership is always verified through user_id — the investment_transaction
    repository joins back to the parent Investment to enforce this.

    No portfolio calculations (CAGR, XIRR, NAV deltas) are performed here —
    those belong to the Financial Engine.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._inv_repo = InvestmentRepository(db)
        self._txn_repo = InvestmentTransactionRepository(db)

    # ==================================================================
    # Investments
    # ==================================================================

    def get_investment(self, investment_id: int, user_id: int) -> Investment:
        """Retrieve a single investment for *user_id*, or raise 404."""
        record = self._inv_repo.get_by_id_for_user(investment_id, user_id)
        if record is None:
            raise ResourceNotFoundError(resource="Investment", identifier=investment_id)
        return record

    def list_investments(
        self,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
        investment_type: InvestmentType | None = None,
    ) -> list[Investment]:
        """List investment records for *user_id* with optional type filter."""
        return self._inv_repo.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            investment_type=investment_type,
        )

    def create_investment(
        self,
        user_id: int,
        *,
        investment_type: InvestmentType,
        name: str,
        principal: Decimal,
        current_value: Decimal,
        purchase_date: date,
        currency: str = "INR",
        quantity: Decimal | None = None,
        maturity_date: date | None = None,
        interest_rate: Decimal | None = None,
        investment_metadata: dict | None = None,
    ) -> Investment:
        """Create a new Investment record for *user_id*."""
        investment = Investment(
            user_id=user_id,
            investment_type=investment_type,
            name=name,
            principal=principal,
            current_value=current_value,
            purchase_date=purchase_date,
            currency=currency,
            quantity=quantity,
            maturity_date=maturity_date,
            interest_rate=interest_rate,
            investment_metadata=investment_metadata,
        )
        with handle_db_exceptions(resource="Investment"):
            self._inv_repo.add(investment)
            self._db.commit()
        self._db.refresh(investment)
        return investment

    def update_investment(
        self,
        investment_id: int,
        user_id: int,
        **fields: object,
    ) -> Investment:
        """Update mutable fields on an existing Investment record."""
        record = self.get_investment(investment_id, user_id)

        allowed = {
            "investment_type", "name", "principal", "current_value",
            "currency", "quantity", "purchase_date", "maturity_date",
            "interest_rate", "investment_metadata",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(record, key, value)

        with handle_db_exceptions(resource="Investment"):
            self._db.commit()
        self._db.refresh(record)
        return record

    def delete_investment(self, investment_id: int, user_id: int) -> None:
        """Hard-delete an Investment and its child transactions (CASCADE)."""
        record = self.get_investment(investment_id, user_id)
        with handle_db_exceptions(resource="Investment"):
            self._inv_repo.delete(record)
            self._db.commit()

    # ==================================================================
    # Investment Transactions
    # ==================================================================

    def get_investment_transaction(
        self, txn_id: int, user_id: int
    ) -> InvestmentTransaction:
        """Retrieve a single investment transaction, verifying parent ownership."""
        record = self._txn_repo.get_by_id_for_user(txn_id, user_id)
        if record is None:
            raise ResourceNotFoundError(
                resource="InvestmentTransaction", identifier=txn_id
            )
        return record

    def list_investment_transactions(
        self,
        investment_id: int,
        user_id: int,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InvestmentTransaction]:
        """List transactions for a specific investment, verifying user ownership."""
        # Ensure the parent investment belongs to this user first.
        self.get_investment(investment_id, user_id)
        return self._txn_repo.list_by_investment_for_user(
            investment_id, user_id, limit=limit, offset=offset
        )

    def create_investment_transaction(
        self,
        investment_id: int,
        user_id: int,
        *,
        transaction_type: InvestmentTransactionType,
        amount: Decimal,
        transaction_date: date,
        quantity: Decimal | None = None,
        price_per_unit: Decimal | None = None,
        txn_metadata: dict | None = None,
    ) -> InvestmentTransaction:
        """Create an InvestmentTransaction, verifying parent investment ownership."""
        # Ensure the parent investment belongs to this user.
        self.get_investment(investment_id, user_id)

        txn = InvestmentTransaction(
            investment_id=investment_id,
            transaction_type=transaction_type,
            amount=amount,
            transaction_date=transaction_date,
            quantity=quantity,
            price_per_unit=price_per_unit,
            txn_metadata=txn_metadata,
        )
        with handle_db_exceptions(resource="InvestmentTransaction"):
            self._txn_repo.add(txn)
            self._db.commit()
        self._db.refresh(txn)
        return txn
