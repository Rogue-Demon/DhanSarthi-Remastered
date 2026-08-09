"""
Comprehensive tests for DhanSarthi core PostgreSQL models and relationships.

Coverage:
1. User / Profile 1:1 relationship and Persona enum validation.
2. Financial ownership structure (User owns all core models).
3. Child relationships (Investment -> InvestmentTransaction, Loan -> LoanPayment).
4. Monetary non-negative constraints.
5. User isolation (separating records belonging to User A and User B).
6. Relationship cascade behavior.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DBAPIError

from app.models.user import User
from app.models.profile import Profile
from app.models.income import Income
from app.models.expense import Expense
from app.models.transaction import Transaction
from app.models.asset import Asset
from app.models.liability import Liability
from app.models.investment import Investment, InvestmentTransaction
from app.models.loan import Loan, LoanPayment
from app.models.goal import Goal
from app.models.budget import Budget
from app.models.enums import (
    Persona,
    RiskProfile,
    IncomeFrequency,
    ExpenseFrequency,
    TransactionType,
    AssetType,
    LiabilityType,
    InvestmentType,
    InvestmentTransactionType,
    LoanType,
    LoanStatus,
    GoalStatus,
    BudgetPeriod,
)


# ===========================================================================
# 1. User & Profile Tests
# ===========================================================================

def test_user_creation_and_profile_relationship(db_session: Session) -> None:
    """A user can be created and has a 1-to-1 relationship with a Profile."""
    user = User(email="test@dhansarthi.com")
    db_session.add(user)
    db_session.flush()

    profile = Profile(
        user_id=user.id,
        display_name="Test Student User",
        persona=Persona.STUDENT,
        country="IND",
        currency="INR",
        risk_profile=RiskProfile.CONSERVATIVE,
        financial_preferences={"dark_mode": True},
    )
    db_session.add(profile)
    db_session.flush()

    # Refresh and assert
    db_session.refresh(user)
    assert user.profile is not None
    assert user.profile.display_name == "Test Student User"
    assert user.profile.persona == Persona.STUDENT
    assert user.profile.user is user


def test_profile_one_to_one_unique_constraint(db_session: Session) -> None:
    """Enforce 1:1 relation; adding a second profile for the same user must fail."""
    user = User(email="test@dhansarthi.com")
    db_session.add(user)
    db_session.flush()

    p1 = Profile(display_name="Profile 1", persona=Persona.STUDENT, user_id=user.id)
    p2 = Profile(display_name="Profile 2", persona=Persona.PROFESSIONAL, user_id=user.id)
    
    db_session.add(p1)
    db_session.flush()
    
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_profile_cascade_delete(db_session: Session) -> None:
    """Deleting a user must CASCADE delete their profile."""
    user = User(email="test_cascade@dhansarthi.com")
    db_session.add(user)
    db_session.flush()

    profile = Profile(
        user_id=user.id,
        display_name="To Be Deleted",
        persona=Persona.PROFESSIONAL,
    )
    db_session.add(profile)
    db_session.flush()

    profile_id = profile.id
    db_session.delete(user)
    db_session.flush()

    # Profile should be gone
    deleted_profile = db_session.query(Profile).filter_by(id=profile_id).first()
    assert deleted_profile is None


# ===========================================================================
# 2. Financial Ownership Tests
# ===========================================================================

@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(email="owner@dhansarthi.com")
    db_session.add(user)
    db_session.flush()
    return user


def test_income_belongs_to_user(db_session: Session, test_user: User) -> None:
    income = Income(
        user_id=test_user.id,
        source="Salary",
        category="Primary",
        amount=Decimal("75000.00"),
        currency="INR",
        frequency=IncomeFrequency.MONTHLY,
        income_date=date(2026, 8, 1),
    )
    db_session.add(income)
    db_session.flush()
    assert income.user is test_user


def test_expense_belongs_to_user(db_session: Session, test_user: User) -> None:
    expense = Expense(
        user_id=test_user.id,
        category="Rent",
        amount=Decimal("15000.00"),
        currency="INR",
        expense_date=date(2026, 8, 1),
        frequency=ExpenseFrequency.MONTHLY,
    )
    db_session.add(expense)
    db_session.flush()
    assert expense.user is test_user


def test_transaction_belongs_to_user(db_session: Session, test_user: User) -> None:
    transaction = Transaction(
        user_id=test_user.id,
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("2500.00"),
        currency="INR",
        category="Groceries",
        transaction_date=date(2026, 8, 2),
        source="Bank Account",
    )
    db_session.add(transaction)
    db_session.flush()
    assert transaction.user is test_user


def test_asset_belongs_to_user(db_session: Session, test_user: User) -> None:
    asset = Asset(
        user_id=test_user.id,
        asset_type=AssetType.GOLD,
        name="Gold Sovereign",
        value=Decimal("55000.00"),
        currency="INR",
        valuation_date=date(2026, 8, 1),
        asset_metadata={"purity": "24K", "weight_grams": 8},
    )
    db_session.add(asset)
    db_session.flush()
    assert asset.user is test_user


def test_liability_belongs_to_user(db_session: Session, test_user: User) -> None:
    liability = Liability(
        user_id=test_user.id,
        liability_type=LiabilityType.CREDIT_CARD,
        name="HDFC CC",
        outstanding_amount=Decimal("12300.50"),
        currency="INR",
        interest_rate=Decimal("0.4200"),
    )
    db_session.add(liability)
    db_session.flush()
    assert liability.user is test_user


def test_investment_belongs_to_user(db_session: Session, test_user: User) -> None:
    investment = Investment(
        user_id=test_user.id,
        investment_type=InvestmentType.STOCK,
        name="TCS",
        principal=Decimal("50000.00"),
        current_value=Decimal("58000.00"),
        currency="INR",
        quantity=Decimal("15.00000000"),
        purchase_date=date(2026, 1, 15),
    )
    db_session.add(investment)
    db_session.flush()
    assert investment.user is test_user


def test_loan_belongs_to_user(db_session: Session, test_user: User) -> None:
    loan = Loan(
        user_id=test_user.id,
        loan_type=LoanType.HOME,
        lender="SBI",
        principal_amount=Decimal("3000000.00"),
        outstanding_amount=Decimal("2800000.00"),
        currency="INR",
        interest_rate=Decimal("0.0850"),
        tenure=240,
        remaining_tenure=228,
        emi=Decimal("26000.00"),
        start_date=date(2025, 8, 1),
    )
    db_session.add(loan)
    db_session.flush()
    assert loan.user is test_user


def test_goal_belongs_to_user(db_session: Session, test_user: User) -> None:
    goal = Goal(
        user_id=test_user.id,
        name="Emergency Fund",
        target_amount=Decimal("150000.00"),
        current_amount=Decimal("45000.00"),
        currency="INR",
        priority=1,
        status=GoalStatus.ACTIVE,
    )
    db_session.add(goal)
    db_session.flush()
    assert goal.user is test_user


def test_budget_belongs_to_user(db_session: Session, test_user: User) -> None:
    budget = Budget(
        user_id=test_user.id,
        category="Dining Out",
        amount=Decimal("5000.00"),
        currency="INR",
        period=BudgetPeriod.MONTHLY,
        start_date=date(2026, 8, 1),
    )
    db_session.add(budget)
    db_session.flush()
    assert budget.user is test_user


# ===========================================================================
# 3. Child Relationships Tests
# ===========================================================================

def test_investment_transaction_belongs_to_investment(db_session: Session, test_user: User) -> None:
    """An InvestmentTransaction belongs to an Investment, and Cascade delete works."""
    inv = Investment(
        user_id=test_user.id,
        investment_type=InvestmentType.MUTUAL_FUND,
        name="Parag Parikh Flexi Cap",
        principal=Decimal("10000.00"),
        current_value=Decimal("10000.00"),
        currency="INR",
        quantity=Decimal("180.25000000"),
        purchase_date=date(2026, 8, 1),
    )
    db_session.add(inv)
    db_session.flush()

    txn = InvestmentTransaction(
        investment_id=inv.id,
        transaction_type=InvestmentTransactionType.BUY,
        amount=Decimal("10000.00"),
        quantity=Decimal("180.25000000"),
        price_per_unit=Decimal("55.47850000"),
        transaction_date=date(2026, 8, 1),
    )
    db_session.add(txn)
    db_session.flush()

    # Verify relationship
    assert txn.investment is inv
    assert txn in inv.transactions

    # Verify CASCADE delete
    inv_id = inv.id
    txn_id = txn.id
    db_session.delete(inv)
    db_session.flush()

    deleted_txn = db_session.query(InvestmentTransaction).filter_by(id=txn_id).first()
    assert deleted_txn is None


def test_loan_payment_belongs_to_loan(db_session: Session, test_user: User) -> None:
    """A LoanPayment belongs to a Loan, and Cascade delete works."""
    loan = Loan(
        user_id=test_user.id,
        loan_type=LoanType.VEHICLE,
        lender="HDFC",
        principal_amount=Decimal("800000.00"),
        outstanding_amount=Decimal("780000.00"),
        currency="INR",
        interest_rate=Decimal("0.0920"),
        tenure=60,
        remaining_tenure=58,
        emi=Decimal("16680.00"),
        start_date=date(2026, 6, 1),
    )
    db_session.add(loan)
    db_session.flush()

    payment = LoanPayment(
        loan_id=loan.id,
        payment_date=date(2026, 8, 1),
        amount=Decimal("16680.00"),
        principal_component=Decimal("10680.00"),
        interest_component=Decimal("6000.00"),
        remaining_balance=Decimal("763320.00"),
    )
    db_session.add(payment)
    db_session.flush()

    # Verify relationship
    assert payment.loan is loan
    assert payment in loan.payments

    # Verify CASCADE delete
    loan_id = loan.id
    payment_id = payment.id
    db_session.delete(loan)
    db_session.flush()

    deleted_payment = db_session.query(LoanPayment).filter_by(id=payment_id).first()
    assert deleted_payment is None


# ===========================================================================
# 4. Monetary and Value Constraints Tests
# ===========================================================================

def test_income_amount_non_negative_constraint(db_session: Session, test_user: User) -> None:
    """Checking database validation constraint for Income amount >= 0."""
    income = Income(
        user_id=test_user.id,
        source="Freelance",
        category="Tech",
        amount=Decimal("-10.00"),  # negative amount violates constraint
        currency="INR",
        frequency=IncomeFrequency.ONE_TIME,
        income_date=date(2026, 8, 1),
    )
    db_session.add(income)
    # SQLAlchemy raises IntegrityError (sqlite check constraint failure)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_expense_amount_non_negative_constraint(db_session: Session, test_user: User) -> None:
    """Expense amount must be non-negative."""
    expense = Expense(
        user_id=test_user.id,
        category="Transport",
        amount=Decimal("-500.00"),
        currency="INR",
        expense_date=date(2026, 8, 1),
    )
    db_session.add(expense)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_transaction_amount_non_negative_constraint(db_session: Session, test_user: User) -> None:
    """Transaction amount must be non-negative."""
    txn = Transaction(
        user_id=test_user.id,
        transaction_type=TransactionType.INCOME,
        amount=Decimal("-100.00"),
        currency="INR",
        transaction_date=date(2026, 8, 1),
    )
    db_session.add(txn)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_loan_principal_positive_constraint(db_session: Session, test_user: User) -> None:
    """Loan principal amount must be strictly positive (> 0)."""
    loan = Loan(
        user_id=test_user.id,
        loan_type=LoanType.PERSONAL,
        lender="Bajaj",
        principal_amount=Decimal("0.00"),  # Violation: principal must be > 0
        outstanding_amount=Decimal("0.00"),
        currency="INR",
        interest_rate=Decimal("0.1200"),
        tenure=12,
        start_date=date(2026, 8, 1),
    )
    db_session.add(loan)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_goal_priority_range_constraint(db_session: Session, test_user: User) -> None:
    """Goal priority must be between 1 and 5 inclusive."""
    goal = Goal(
        user_id=test_user.id,
        name="House Downpayment",
        target_amount=Decimal("1000000.00"),
        current_amount=Decimal("0.00"),
        currency="INR",
        priority=6,  # Violation: must be between 1 and 5
        status=GoalStatus.ACTIVE,
    )
    db_session.add(goal)
    with pytest.raises(IntegrityError):
        db_session.flush()


# ===========================================================================
# 5. User Isolation Tests
# ===========================================================================

def test_user_isolation_guaranteed(db_session: Session) -> None:
    """Demonstrate that records for User A are separate and distinguishable from User B."""
    # Create two users
    user_a = User(email="user_a@dhansarthi.com")
    user_b = User(email="user_b@dhansarthi.com")
    db_session.add_all([user_a, user_b])
    db_session.flush()

    # Create one transaction for each
    txn_a = Transaction(
        user_id=user_a.id,
        transaction_type=TransactionType.INCOME,
        amount=Decimal("5000.00"),
        currency="INR",
        category="Freelance",
        transaction_date=date(2026, 8, 1),
        description="User A Income",
    )
    txn_b = Transaction(
        user_id=user_b.id,
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("150.00"),
        currency="INR",
        category="Coffee",
        transaction_date=date(2026, 8, 1),
        description="User B Expense",
    )
    db_session.add_all([txn_a, txn_b])
    db_session.flush()

    # Verify query isolation: Querying User A's transactions yields only User A's transaction
    txns_a_db = db_session.query(Transaction).filter_by(user_id=user_a.id).all()
    assert len(txns_a_db) == 1
    assert txns_a_db[0].description == "User A Income"
    assert txns_a_db[0].user_id != user_b.id

    txns_b_db = db_session.query(Transaction).filter_by(user_id=user_b.id).all()
    assert len(txns_b_db) == 1
    assert txns_b_db[0].description == "User B Expense"
    assert txns_b_db[0].user_id != user_a.id

    # Verify isolation checks
    assert txn_a.user_id != txn_b.user_id
