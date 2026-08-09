"""
Repository package for DhanSarthi.

Repositories encapsulate all SQLAlchemy queries so that route handlers and
service functions remain free of raw database access patterns.

The preferred call chain is:

    FastAPI route
        ↓
    Service (business logic)
        ↓
    Repository (database queries)
        ↓
    SQLAlchemy Session
        ↓
    PostgreSQL
"""

from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.profile_repository import ProfileRepository
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

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ProfileRepository",
    "IncomeRepository",
    "ExpenseRepository",
    "TransactionRepository",
    "AssetRepository",
    "LiabilityRepository",
    "InvestmentRepository",
    "InvestmentTransactionRepository",
    "LoanRepository",
    "LoanPaymentRepository",
    "GoalRepository",
    "BudgetRepository",
]
