"""
Service package for DhanSarthi.

Services implement business logic and coordinate data access through
repositories.  They form the transaction boundary — each service method
is responsible for calling ``db.commit()`` on success and letting the
``handle_db_exceptions`` context manager translate database errors into
safe application exceptions.

The preferred call chain is:

    FastAPI route
        ↓
    Service (business logic, ownership checks, commit/rollback)
        ↓
    Repository (database queries, flush only)
        ↓
    SQLAlchemy Session
        ↓
    PostgreSQL
"""

from app.services.auth_service import AuthService
from app.services.income_service import IncomeService
from app.services.expense_service import ExpenseService
from app.services.transaction_service import TransactionService
from app.services.asset_service import AssetService
from app.services.liability_service import LiabilityService
from app.services.investment_service import InvestmentService
from app.services.loan_service import LoanService
from app.services.goal_service import GoalService
from app.services.budget_service import BudgetService
from app.services.financial_service import FinancialService
from app.services.profile_service import ProfileService
from app.services.financial_context_service import FinancialContextService
from app.services.dashboard_service import DashboardService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.document_import_service import FinancialDocumentImportService
from app.services.financial_intelligence_service import FinancialIntelligenceService
from app.services.report_service import ReportService

__all__ = [
    "AuthService",
    "IncomeService",
    "ExpenseService",
    "TransactionService",
    "AssetService",
    "LiabilityService",
    "InvestmentService",
    "LoanService",
    "GoalService",
    "BudgetService",
    "FinancialService",
    "ProfileService",
    "FinancialContextService",
    "DashboardService",
    "ConversationService",
    "DocumentService",
    "FinancialDocumentImportService",
    "FinancialIntelligenceService",
    "ReportService",
]


