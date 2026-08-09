"""
DhanSarthi SQLAlchemy model registry.

Every model must be imported here so that:
1. Alembic autogenerate discovers all tables via ``Base.metadata``.
2. SQLAlchemy resolves all forward-referenced relationships correctly.
3. Application code can import models from a single entry point.

Import order: User first (no FK dependencies), then models that reference it,
then child models (InvestmentTransaction, LoanPayment) last.
"""

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

__all__ = [
    "User",
    "Profile",
    "Income",
    "Expense",
    "Transaction",
    "Asset",
    "Liability",
    "Investment",
    "InvestmentTransaction",
    "Loan",
    "LoanPayment",
    "Goal",
    "Budget",
]
