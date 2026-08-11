"""Service layer tests for DhanSarthi Phase 4.

Tests service methods for:
- Ownership isolation (User A cannot access User B's records via service)
- ResourceNotFoundError on missing/wrong-user lookups
- Create, update, and delete flows
- Soft-delete vs hard-delete behaviour
- Parent-child ownership chains (Investment → InvestmentTransaction, Loan → LoanPayment)
"""

import os
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import itertools
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.database import Base, engine, SessionLocal
from app.core.exceptions import ResourceNotFoundError
from app.models.enums import (
    AssetType,
    BudgetPeriod,
    GoalStatus,
    IncomeFrequency,
    InvestmentTransactionType,
    InvestmentType,
    LoanStatus,
    LoanType,
    TransactionType,
)
from app.models.user import User

from app.services.income_service import IncomeService
from app.services.expense_service import ExpenseService
from app.services.transaction_service import TransactionService
from app.services.asset_service import AssetService
from app.services.liability_service import LiabilityService
from app.services.investment_service import InvestmentService
from app.services.loan_service import LoanService
from app.services.goal_service import GoalService
from app.services.budget_service import BudgetService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_counter = itertools.count(1)




@pytest.fixture
def db() -> Session:
    """Provide a session that uses a SAVEPOINT so that service-layer
    commit() calls are contained and rolled back after the test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Start a nested savepoint; when service code calls session.commit()
    # it only releases the savepoint, not the outer transaction.
    nested = connection.begin_nested()

    # After every commit(), automatically restart a new savepoint.
    from sqlalchemy import event

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction_inner):
        if transaction_inner.nested and not transaction_inner.parent.nested:
            session.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def two_users(db: Session):
    n = next(_counter)
    u1 = User(email=f"svc_alice_{n}@test.com", is_active=True)
    u2 = User(email=f"svc_bob_{n}@test.com", is_active=True)
    db.add_all([u1, u2])
    db.flush()
    return u1.id, u2.id


# ---------------------------------------------------------------------------
# Income Service
# ---------------------------------------------------------------------------

class TestIncomeService:
    def test_create_and_get(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = IncomeService(db)
        inc = svc.create_income(uid_a, source="Job", amount=Decimal("50000"), income_date=date(2025, 1, 15))
        assert inc.id is not None
        assert inc.user_id == uid_a

        fetched = svc.get_income(inc.id, uid_a)
        assert fetched.source == "Job"

    def test_ownership_isolation(self, db: Session, two_users):
        uid_a, uid_b = two_users
        svc = IncomeService(db)
        inc = svc.create_income(uid_a, source="A-only", amount=Decimal("1000"), income_date=date(2025, 2, 1))
        with pytest.raises(ResourceNotFoundError):
            svc.get_income(inc.id, uid_b)

    def test_update(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = IncomeService(db)
        inc = svc.create_income(uid_a, source="Old", amount=Decimal("1000"), income_date=date(2025, 3, 1))
        updated = svc.update_income(inc.id, uid_a, source="New")
        assert updated.source == "New"

    def test_soft_delete(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = IncomeService(db)
        inc = svc.create_income(uid_a, source="ToDelete", amount=Decimal("500"), income_date=date(2025, 4, 1))
        svc.delete_income(inc.id, uid_a)
        # Should no longer be retrievable
        with pytest.raises(ResourceNotFoundError):
            svc.get_income(inc.id, uid_a)

    def test_not_found(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = IncomeService(db)
        with pytest.raises(ResourceNotFoundError):
            svc.get_income(999999, uid_a)


# ---------------------------------------------------------------------------
# Expense Service
# ---------------------------------------------------------------------------

class TestExpenseService:
    def test_create_and_soft_delete(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = ExpenseService(db)
        exp = svc.create_expense(uid_a, category="Food", amount=Decimal("500"), expense_date=date(2025, 1, 10))
        assert exp.id is not None
        svc.delete_expense(exp.id, uid_a)
        with pytest.raises(ResourceNotFoundError):
            svc.get_expense(exp.id, uid_a)

    def test_ownership_isolation(self, db: Session, two_users):
        uid_a, uid_b = two_users
        svc = ExpenseService(db)
        exp = svc.create_expense(uid_a, category="Transport", amount=Decimal("200"), expense_date=date(2025, 1, 5))
        with pytest.raises(ResourceNotFoundError):
            svc.get_expense(exp.id, uid_b)


# ---------------------------------------------------------------------------
# Transaction Service
# ---------------------------------------------------------------------------

class TestTransactionService:
    def test_create_and_list_with_filter(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = TransactionService(db)
        svc.create_transaction(uid_a, transaction_type=TransactionType.INCOME, amount=Decimal("5000"), transaction_date=date(2025, 1, 1))
        svc.create_transaction(uid_a, transaction_type=TransactionType.EXPENSE, amount=Decimal("1000"), transaction_date=date(2025, 1, 2))
        results = svc.list_transactions(uid_a, transaction_type=TransactionType.INCOME)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Asset Service
# ---------------------------------------------------------------------------

class TestAssetService:
    def test_create_and_hard_delete(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = AssetService(db)
        asset = svc.create_asset(uid_a, asset_type=AssetType.GOLD, name="Gold", value=Decimal("100000"), valuation_date=date(2025, 1, 1))
        assert asset.id is not None
        svc.delete_asset(asset.id, uid_a)
        with pytest.raises(ResourceNotFoundError):
            svc.get_asset(asset.id, uid_a)


# ---------------------------------------------------------------------------
# Liability Service
# ---------------------------------------------------------------------------

class TestLiabilityService:
    def test_create_and_update(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = LiabilityService(db)
        liab = svc.create_liability(uid_a, liability_type="CREDIT_CARD", name="HDFC CC", outstanding_amount=Decimal("25000"))
        updated = svc.update_liability(liab.id, uid_a, outstanding_amount=Decimal("20000"))
        assert updated.outstanding_amount == Decimal("20000")


# ---------------------------------------------------------------------------
# Investment Service
# ---------------------------------------------------------------------------

class TestInvestmentService:
    def test_create_investment_and_transaction(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = InvestmentService(db)

        inv = svc.create_investment(
            uid_a,
            investment_type=InvestmentType.STOCK,
            name="TCS",
            principal=Decimal("10000"),
            current_value=Decimal("12000"),
            purchase_date=date(2025, 1, 1),
        )
        assert inv.id is not None

        txn = svc.create_investment_transaction(
            inv.id, uid_a,
            transaction_type=InvestmentTransactionType.BUY,
            amount=Decimal("10000"),
            transaction_date=date(2025, 1, 1),
        )
        assert txn.investment_id == inv.id

    def test_child_transaction_ownership_isolation(self, db: Session, two_users):
        uid_a, uid_b = two_users
        svc = InvestmentService(db)

        inv = svc.create_investment(uid_a, investment_type=InvestmentType.STOCK, name="Infosys", principal=Decimal("5000"), current_value=Decimal("6000"), purchase_date=date(2025, 2, 1))
        txn = svc.create_investment_transaction(inv.id, uid_a, transaction_type=InvestmentTransactionType.BUY, amount=Decimal("5000"), transaction_date=date(2025, 2, 1))

        # User B cannot access User A's investment transaction
        with pytest.raises(ResourceNotFoundError):
            svc.get_investment_transaction(txn.id, uid_b)

    def test_cannot_add_txn_to_other_users_investment(self, db: Session, two_users):
        uid_a, uid_b = two_users
        svc = InvestmentService(db)

        inv = svc.create_investment(uid_a, investment_type=InvestmentType.FD, name="SBI FD", principal=Decimal("50000"), current_value=Decimal("52000"), purchase_date=date(2025, 3, 1))

        # User B cannot add transactions to User A's investment
        with pytest.raises(ResourceNotFoundError):
            svc.create_investment_transaction(inv.id, uid_b, transaction_type=InvestmentTransactionType.INTEREST, amount=Decimal("2000"), transaction_date=date(2025, 6, 1))


# ---------------------------------------------------------------------------
# Loan Service
# ---------------------------------------------------------------------------

class TestLoanService:
    def test_create_loan_and_payment(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = LoanService(db)

        loan = svc.create_loan(
            uid_a,
            loan_type=LoanType.HOME,
            lender="SBI",
            principal_amount=Decimal("5000000"),
            outstanding_amount=Decimal("4500000"),
            interest_rate=Decimal("0.0850"),
            tenure=240,
            start_date=date(2024, 1, 1),
        )
        assert loan.id is not None
        assert loan.status == LoanStatus.ACTIVE

        payment = svc.create_loan_payment(
            loan.id, uid_a,
            payment_date=date(2024, 2, 1),
            amount=Decimal("45000"),
        )
        assert payment.loan_id == loan.id

    def test_child_payment_ownership_isolation(self, db: Session, two_users):
        uid_a, uid_b = two_users
        svc = LoanService(db)

        loan = svc.create_loan(uid_a, loan_type=LoanType.PERSONAL, lender="ICICI", principal_amount=Decimal("200000"), outstanding_amount=Decimal("180000"), interest_rate=Decimal("0.1100"), tenure=36, start_date=date(2024, 6, 1))
        payment = svc.create_loan_payment(loan.id, uid_a, payment_date=date(2024, 7, 1), amount=Decimal("6500"))

        # User B cannot access User A's loan payment
        with pytest.raises(ResourceNotFoundError):
            svc.get_loan_payment(payment.id, uid_b)

    def test_cannot_add_payment_to_other_users_loan(self, db: Session, two_users):
        uid_a, uid_b = two_users
        svc = LoanService(db)

        loan = svc.create_loan(uid_a, loan_type=LoanType.VEHICLE, lender="Axis", principal_amount=Decimal("800000"), outstanding_amount=Decimal("750000"), interest_rate=Decimal("0.0950"), tenure=60, start_date=date(2024, 3, 1))

        # User B cannot add payments to User A's loan
        with pytest.raises(ResourceNotFoundError):
            svc.create_loan_payment(loan.id, uid_b, payment_date=date(2024, 4, 1), amount=Decimal("15000"))


# ---------------------------------------------------------------------------
# Goal Service
# ---------------------------------------------------------------------------

class TestGoalService:
    def test_create_and_update(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = GoalService(db)

        goal = svc.create_goal(uid_a, name="Emergency Fund", target_amount=Decimal("300000"), priority=1)
        assert goal.status == GoalStatus.ACTIVE

        updated = svc.update_goal(goal.id, uid_a, current_amount=Decimal("50000"))
        assert updated.current_amount == Decimal("50000")

    def test_ownership_isolation(self, db: Session, two_users):
        uid_a, uid_b = two_users
        svc = GoalService(db)
        goal = svc.create_goal(uid_a, name="Vacation", target_amount=Decimal("100000"))
        with pytest.raises(ResourceNotFoundError):
            svc.get_goal(goal.id, uid_b)


# ---------------------------------------------------------------------------
# Budget Service
# ---------------------------------------------------------------------------

class TestBudgetService:
    def test_create_and_list(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = BudgetService(db)
        svc.create_budget(uid_a, category="Food", amount=Decimal("15000"), period=BudgetPeriod.MONTHLY, start_date=date(2025, 1, 1))
        svc.create_budget(uid_a, category="Entertainment", amount=Decimal("5000"), period=BudgetPeriod.MONTHLY, start_date=date(2025, 1, 1))
        results = svc.list_budgets(uid_a)
        assert len(results) == 2

    def test_hard_delete(self, db: Session, two_users):
        uid_a, _ = two_users
        svc = BudgetService(db)
        budget = svc.create_budget(uid_a, category="Transport", amount=Decimal("3000"), period=BudgetPeriod.MONTHLY, start_date=date(2025, 1, 1))
        svc.delete_budget(budget.id, uid_a)
        with pytest.raises(ResourceNotFoundError):
            svc.get_budget(budget.id, uid_a)

    def test_ownership_isolation(self, db: Session, two_users):
        uid_a, uid_b = two_users
        svc = BudgetService(db)
        budget = svc.create_budget(uid_a, category="Gym", amount=Decimal("2000"), period=BudgetPeriod.MONTHLY, start_date=date(2025, 2, 1))
        with pytest.raises(ResourceNotFoundError):
            svc.get_budget(budget.id, uid_b)
