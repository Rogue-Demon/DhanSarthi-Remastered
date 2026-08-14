"""FastAPI dependencies for DhanSarthi API routes.

Authentication dependencies use JWT Bearer tokens to resolve the
current authenticated user.  All user-owned endpoints receive the
verified ``user_id`` through ``get_current_user_id``.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services import (
    AssetService,
    AuthService,
    BudgetService,
    ConversationService,
    DashboardService,
    ExpenseService,
    FinancialContextService,
    FinancialService,
    GoalService,
    IncomeService,
    InvestmentService,
    LiabilityService,
    LoanService,
    ProfileService,
    TransactionService,
    DocumentService,
    FinancialDocumentImportService,
    FinancialIntelligenceService,
)
from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.providers.mock import MockLLMProvider
from app.ai.rag.mock import MockRAGRetriever
from app.core.config import settings


# ---------------------------------------------------------------------------
# OAuth2 bearer scheme — used by OpenAPI docs and token extraction
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ---------------------------------------------------------------------------
# Authenticated user dependencies
# ---------------------------------------------------------------------------


def get_current_user(
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
) -> User:
    """Resolve the authenticated user from a JWT Bearer token.

    Flow:
        Request → Authorization: Bearer <token> → Decode → Load User → Validate Active

    Raises ``401 Unauthorized`` if:
        - Token is missing, malformed, or expired.
        - Token subject is missing.
        - User no longer exists.
        - User is inactive.

    Error messages are generic to avoid leaking JWT implementation details.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user


def get_current_user_id(
    current_user: User = Depends(get_current_user),
) -> int:
    """Return the authenticated user's ID.

    This is the primary dependency used by all user-owned financial endpoints.
    It replaces the former temporary ``X-User-ID`` header mechanism.
    """
    return current_user.id


# ---------------------------------------------------------------------------
# Service factories
# ---------------------------------------------------------------------------


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_profile_service(db: Session = Depends(get_db)) -> ProfileService:
    return ProfileService(db)


def get_income_service(db: Session = Depends(get_db)) -> IncomeService:
    return IncomeService(db)


def get_expense_service(db: Session = Depends(get_db)) -> ExpenseService:
    return ExpenseService(db)


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    return TransactionService(db)


def get_asset_service(db: Session = Depends(get_db)) -> AssetService:
    return AssetService(db)


def get_liability_service(db: Session = Depends(get_db)) -> LiabilityService:
    return LiabilityService(db)


def get_investment_service(db: Session = Depends(get_db)) -> InvestmentService:
    return InvestmentService(db)


def get_loan_service(db: Session = Depends(get_db)) -> LoanService:
    return LoanService(db)


def get_goal_service(db: Session = Depends(get_db)) -> GoalService:
    return GoalService(db)


def get_budget_service(db: Session = Depends(get_db)) -> BudgetService:
    return BudgetService(db)


def get_financial_service(db: Session = Depends(get_db)) -> FinancialService:
    return FinancialService(db)


def get_financial_context_service(db: Session = Depends(get_db)) -> FinancialContextService:
    return FinancialContextService(db)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def get_conversation_service(db: Session = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.retriever import PostgresRAGRetriever
from app.ai.rag.base import RAGRetriever


def get_llm_provider():
    if settings.ai_provider == "huggingface":
        return HuggingFaceProvider()
    return MockLLMProvider()


def get_embedding_provider():
    if settings.embedding_provider == "huggingface":
        return HuggingFaceProvider()
    return MockEmbeddingProvider()


def get_rag_retriever(
    db: Session = Depends(get_db),
    embedding_provider=Depends(get_embedding_provider),
) -> RAGRetriever:
    return PostgresRAGRetriever(db=db, embedding_provider=embedding_provider)


def get_safety_validator() -> SimpleSafetyValidator:
    return SimpleSafetyValidator()


def get_context_builder() -> AIContextBuilder:
    return AIContextBuilder()


def get_financial_intelligence_service(db: Session = Depends(get_db)) -> FinancialIntelligenceService:
    return FinancialIntelligenceService(db)


from app.market_data.service import MarketDataService
from app.market_data.cache import MarketDataCache

# Global cache instance for the application lifecycle
market_data_cache = MarketDataCache()


def get_market_data_service() -> MarketDataService:
    return MarketDataService(cache=market_data_cache)


def get_ai_advisor_service(
    db: Session = Depends(get_db),
    llm_provider=Depends(get_llm_provider),
    rag_retriever=Depends(get_rag_retriever),
    safety_validator=Depends(get_safety_validator),
    context_builder=Depends(get_context_builder),
    dashboard_service=Depends(get_dashboard_service),
    conversation_service=Depends(get_conversation_service),
    financial_intelligence_service=Depends(get_financial_intelligence_service),
    market_data_service=Depends(get_market_data_service),
) -> AIAdvisorService:
    return AIAdvisorService(
        db=db,
        llm_provider=llm_provider,
        rag_retriever=rag_retriever,
        safety_validator=safety_validator,
        context_builder=context_builder,
        dashboard_service=dashboard_service,
        conversation_service=conversation_service,
        financial_intelligence_service=financial_intelligence_service,
        market_data_service=market_data_service,
    )


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


def get_document_import_service(db: Session = Depends(get_db)) -> FinancialDocumentImportService:
    return FinancialDocumentImportService(db)


from app.services.report_service import ReportService


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


