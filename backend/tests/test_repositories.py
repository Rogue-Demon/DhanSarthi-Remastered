"""Repository tests for DhanSarthi Phase 4.

Tests repository methods for:
- User-scoped read isolation (User A cannot see User B's records)
- Filter correctness (type, status, date range, category)
- Soft-delete awareness (Income/Expense repositories skip deleted_at rows)
- Parent ownership verification (InvestmentTransaction, LoanPayment)
"""

import os
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.database import Base, engine, SessionLocal
from app.models.enums import (
    AssetType,
    BudgetPeriod,
    ExpenseFrequency,
    GoalStatus,
    IncomeFrequency,
    InvestmentTransactionType,
    InvestmentType,
    LiabilityType,
    LoanStatus,
    LoanType,
    TransactionType,
)
from app.models.user import User
from app.models.income import Income
from app.models.expense import Expense
from app.models.transaction import Transaction
from app.models.asset import Asset
from app.models.liability import Liability
from app.models.investment import Investment, InvestmentTransaction
from app.models.loan import Loan, LoanPayment
from app.models.goal import Goal
from app.models.budget import Budget

from app.repositories.user_repository import UserRepository
from app.repositories.income_repository import IncomeRepository
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.liability_repository import LiabilityRepository
from app.repositories.investment_repository import InvestmentRepository
from app.repositories.investment_transaction_repository import InvestmentTransactionRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.loan_payment_repository import LoanPaymentRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.budget_repository import BudgetRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def setup_repo_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    session.begin()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def two_users(db: Session):
    """Create two users and return their IDs."""
    u1 = User(email="repo_alice@test.com", is_active=True)
    u2 = User(email="repo_bob@test.com", is_active=True)
    db.add_all([u1, u2])
    db.flush()
    return u1.id, u2.id


# ---------------------------------------------------------------------------
# Income Repository
# ---------------------------------------------------------------------------

class TestIncomeRepository:
    def test_list_for_user_filters_by_user(self, db: Session, two_users):
        uid_a, uid_b = two_users
        db.add(Income(user_id=uid_a, source="Job", category="Salary", amount=Decimal("50000"), currency="INR", frequency=IncomeFrequency.MONTHLY, income_date=date(2025, 1, 15)))
        db.add(Income(user_id=uid_b, source="Freelance", category="Consulting", amount=Decimal("20000"), currency="INR", frequency=IncomeFrequency.ONE_TIME, income_date=date(2025, 1, 15)))
        db.flush()

        repo = IncomeRepository(db)
        results = repo.list_for_user(uid_a)
        assert len(results) == 1
        assert results[0].source == "Job"

    def test_soft_deleted_records_excluded(self, db: Session, two_users):
        uid_a, _ = two_users
        inc = Income(user_id=uid_a, source="Deleted", category="Other", amount=Decimal("100"), currency="INR", frequency=IncomeFrequency.ONE_TIME, income_date=date(2025, 2, 1), deleted_at=datetime.now(timezone.utc))
        db.add(inc)
        db.flush()

        repo = IncomeRepository(db)
        assert repo.get_by_id_for_user(inc.id, uid_a) is None
        assert len(repo.list_for_user(uid_a)) == 0

    def test_filter_by_category(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Income(user_id=uid_a, source="A", category="Salary", amount=Decimal("1000"), currency="INR", frequency=IncomeFrequency.MONTHLY, income_date=date(2025, 3, 1)))
        db.add(Income(user_id=uid_a, source="B", category="Rent", amount=Decimal("500"), currency="INR", frequency=IncomeFrequency.MONTHLY, income_date=date(2025, 3, 1)))
        db.flush()

        repo = IncomeRepository(db)
        results = repo.list_for_user(uid_a, category="Salary")
        assert all(r.category == "Salary" for r in results)


# ---------------------------------------------------------------------------
# Expense Repository
# ---------------------------------------------------------------------------

class TestExpenseRepository:
    def test_user_isolation(self, db: Session, two_users):
        uid_a, uid_b = two_users
        db.add(Expense(user_id=uid_a, category="Food", amount=Decimal("500"), currency="INR", expense_date=date(2025, 1, 10)))
        db.add(Expense(user_id=uid_b, category="Transport", amount=Decimal("200"), currency="INR", expense_date=date(2025, 1, 10)))
        db.flush()

        repo = ExpenseRepository(db)
        assert len(repo.list_for_user(uid_a)) == 1
        assert repo.list_for_user(uid_a)[0].category == "Food"


# ---------------------------------------------------------------------------
# Transaction Repository
# ---------------------------------------------------------------------------

class TestTransactionRepository:
    def test_filter_by_type(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Transaction(user_id=uid_a, transaction_type=TransactionType.INCOME, amount=Decimal("1000"), currency="INR", category="Salary", transaction_date=date(2025, 1, 1)))
        db.add(Transaction(user_id=uid_a, transaction_type=TransactionType.EXPENSE, amount=Decimal("200"), currency="INR", category="Food", transaction_date=date(2025, 1, 2)))
        db.flush()

        repo = TransactionRepository(db)
        results = repo.list_for_user(uid_a, transaction_type=TransactionType.INCOME)
        assert len(results) == 1
        assert results[0].transaction_type == TransactionType.INCOME


# ---------------------------------------------------------------------------
# Asset Repository
# ---------------------------------------------------------------------------

class TestAssetRepository:
    def test_filter_by_type(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Asset(user_id=uid_a, asset_type=AssetType.GOLD, name="Gold Coins", value=Decimal("100000"), currency="INR", valuation_date=date(2025, 1, 1)))
        db.add(Asset(user_id=uid_a, asset_type=AssetType.CASH, name="Savings", value=Decimal("50000"), currency="INR", valuation_date=date(2025, 1, 1)))
        db.flush()

        repo = AssetRepository(db)
        results = repo.list_for_user(uid_a, asset_type=AssetType.GOLD)
        assert len(results) == 1
        assert results[0].name == "Gold Coins"


# ---------------------------------------------------------------------------
# Liability Repository
# ---------------------------------------------------------------------------

class TestLiabilityRepository:
    def test_user_isolation(self, db: Session, two_users):
        uid_a, uid_b = two_users
        db.add(Liability(user_id=uid_a, liability_type=LiabilityType.CREDIT_CARD, name="HDFC CC", outstanding_amount=Decimal("25000"), currency="INR"))
        db.add(Liability(user_id=uid_b, liability_type=LiabilityType.PERSONAL_DEBT, name="Friend loan", outstanding_amount=Decimal("5000"), currency="INR"))
        db.flush()

        repo = LiabilityRepository(db)
        assert len(repo.list_for_user(uid_a)) == 1
        assert repo.list_for_user(uid_a)[0].name == "HDFC CC"


# ---------------------------------------------------------------------------
# Investment + InvestmentTransaction Repository
# ---------------------------------------------------------------------------

class TestInvestmentRepository:
    def test_filter_by_type(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Investment(user_id=uid_a, investment_type=InvestmentType.STOCK, name="TCS", principal=Decimal("10000"), current_value=Decimal("12000"), currency="INR", purchase_date=date(2025, 1, 1)))
        db.add(Investment(user_id=uid_a, investment_type=InvestmentType.FD, name="SBI FD", principal=Decimal("50000"), current_value=Decimal("52000"), currency="INR", purchase_date=date(2025, 1, 1)))
        db.flush()

        repo = InvestmentRepository(db)
        results = repo.list_for_user(uid_a, investment_type=InvestmentType.STOCK)
        assert len(results) == 1
        assert results[0].name == "TCS"


class TestInvestmentTransactionRepository:
    def test_parent_ownership_enforcement(self, db: Session, two_users):
        """InvestmentTransaction retrieval must verify the parent Investment
        belongs to the requesting user."""
        uid_a, uid_b = two_users
        inv = Investment(user_id=uid_a, investment_type=InvestmentType.STOCK, name="Infosys", principal=Decimal("5000"), current_value=Decimal("6000"), currency="INR", purchase_date=date(2025, 1, 1))
        db.add(inv)
        db.flush()

        txn = InvestmentTransaction(investment_id=inv.id, transaction_type=InvestmentTransactionType.BUY, amount=Decimal("5000"), transaction_date=date(2025, 1, 1))
        db.add(txn)
        db.flush()

        repo = InvestmentTransactionRepository(db)
        # Owner can see it
        assert repo.get_by_id_for_user(txn.id, uid_a) is not None
        # Non-owner cannot
        assert repo.get_by_id_for_user(txn.id, uid_b) is None


# ---------------------------------------------------------------------------
# Loan + LoanPayment Repository
# ---------------------------------------------------------------------------

class TestLoanRepository:
    def test_filter_by_status(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Loan(user_id=uid_a, loan_type=LoanType.HOME, lender="SBI", principal_amount=Decimal("5000000"), outstanding_amount=Decimal("4500000"), interest_rate=Decimal("0.0850"), tenure=240, start_date=date(2024, 1, 1), status=LoanStatus.ACTIVE))
        db.add(Loan(user_id=uid_a, loan_type=LoanType.PERSONAL, lender="HDFC", principal_amount=Decimal("100000"), outstanding_amount=Decimal("0"), interest_rate=Decimal("0.1200"), tenure=24, start_date=date(2023, 1, 1), status=LoanStatus.CLOSED))
        db.flush()

        repo = LoanRepository(db)
        active = repo.list_for_user(uid_a, status=LoanStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].lender == "SBI"


class TestLoanPaymentRepository:
    def test_parent_ownership_enforcement(self, db: Session, two_users):
        """LoanPayment retrieval must verify the parent Loan belongs to the
        requesting user."""
        uid_a, uid_b = two_users
        loan = Loan(user_id=uid_a, loan_type=LoanType.PERSONAL, lender="ICICI", principal_amount=Decimal("200000"), outstanding_amount=Decimal("180000"), interest_rate=Decimal("0.1100"), tenure=36, start_date=date(2024, 6, 1), status=LoanStatus.ACTIVE)
        db.add(loan)
        db.flush()

        payment = LoanPayment(loan_id=loan.id, payment_date=date(2024, 7, 1), amount=Decimal("6500"))
        db.add(payment)
        db.flush()

        repo = LoanPaymentRepository(db)
        # Owner can see it
        assert repo.get_by_id_for_user(payment.id, uid_a) is not None
        # Non-owner cannot
        assert repo.get_by_id_for_user(payment.id, uid_b) is None


# ---------------------------------------------------------------------------
# Goal Repository
# ---------------------------------------------------------------------------

class TestGoalRepository:
    def test_filter_by_status_and_priority(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Goal(user_id=uid_a, name="Emergency Fund", target_amount=Decimal("300000"), priority=1, status=GoalStatus.ACTIVE))
        db.add(Goal(user_id=uid_a, name="Vacation", target_amount=Decimal("100000"), priority=3, status=GoalStatus.PAUSED))
        db.flush()

        repo = GoalRepository(db)
        active = repo.list_for_user(uid_a, status=GoalStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].name == "Emergency Fund"

        high_priority = repo.list_for_user(uid_a, priority=1)
        assert len(high_priority) == 1

    def test_filter_by_target_date(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Goal(user_id=uid_a, name="Near", target_amount=Decimal("50000"), target_date=date(2025, 6, 1)))
        db.add(Goal(user_id=uid_a, name="Far", target_amount=Decimal("500000"), target_date=date(2030, 1, 1)))
        db.flush()

        repo = GoalRepository(db)
        before_2026 = repo.list_for_user(uid_a, target_date_before=date(2026, 1, 1))
        assert len(before_2026) == 1
        assert before_2026[0].name == "Near"


# ---------------------------------------------------------------------------
# Budget Repository
# ---------------------------------------------------------------------------

class TestBudgetRepository:
    def test_filter_by_category_and_period(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Budget(user_id=uid_a, category="Food", amount=Decimal("15000"), period=BudgetPeriod.MONTHLY, start_date=date(2025, 1, 1)))
        db.add(Budget(user_id=uid_a, category="Entertainment", amount=Decimal("5000"), period=BudgetPeriod.MONTHLY, start_date=date(2025, 1, 1)))
        db.flush()

        repo = BudgetRepository(db)
        food = repo.list_for_user(uid_a, category="Food")
        assert len(food) == 1

        monthly = repo.list_for_user(uid_a, period=BudgetPeriod.MONTHLY)
        assert len(monthly) == 2

    def test_active_on_filter(self, db: Session, two_users):
        uid_a, _ = two_users
        db.add(Budget(user_id=uid_a, category="Travel", amount=Decimal("30000"), period=BudgetPeriod.CUSTOM, start_date=date(2025, 3, 1), end_date=date(2025, 3, 31)))
        db.flush()

        repo = BudgetRepository(db)
        # Mid-March should match
        active = repo.list_for_user(uid_a, active_on=date(2025, 3, 15))
        assert len(active) == 1

        # April should not match
        inactive = repo.list_for_user(uid_a, active_on=date(2025, 4, 15))
        assert len(inactive) == 0
