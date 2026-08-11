"""
Integration tests for market data AI advisor context building and security.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date
import pytest
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch

from app.models.user import User
from app.models.profile import Profile
from app.models.enums import Persona, RiskProfile, InvestmentType
from app.models.investment import Investment
from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.schemas.advisor import RetrievedDocument
from app.schemas.dashboard import DashboardResponse
from app.market_data.service import MarketDataService
from app.market_data.exceptions import InvalidSymbolError


def _seed_user(db: Session, user_id: int) -> User:
    u = User(id=user_id, email=f"user_{user_id}@test.com", password_hash="hash")
    db.add(u)
    db.add(
        Profile(
            user_id=user_id,
            display_name=f"User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
    )
    db.flush()
    return u


@pytest.mark.anyio
async def test_ai_advisor_intent_detection():
    # Verify that query scan extracts symbols correctly
    service = AIAdvisorService(
        db=None,
        llm_provider=None,
        rag_retriever=None,
        safety_validator=None,
        context_builder=None,
        dashboard_service=None,
        market_data_service=MarketDataService(),
    )
    
    # 1. Ask about stock quote
    data = await service._retrieve_live_market_data("What is the price of RELIANCE.NS?", 999)
    assert data is not None
    assert "stocks" in data
    assert data["stocks"][0]["symbol"] == "RELIANCE.NS"

    # 2. Ask about MF nav
    data = await service._retrieve_live_market_data("What is the NAV of scheme 119063?", 999)
    assert data is not None
    assert "mutual_funds" in data
    assert data["mutual_funds"][0]["scheme_id"] == "119063"


@pytest.mark.anyio
async def test_rag_vs_live_data_precedence():
    builder = AIContextBuilder()
    
    # Create mock RAG doc saying price = 100
    rag_docs = [
        RetrievedDocument(
            document_id="rag1",
            title="Old Quote Info",
            content="Stock price is 100",
            source="Stale Doc",
        )
    ]
    
    # Create live stock data saying price = 150
    live_data = {
        "stocks": [
            {
                "symbol": "RELIANCE.NS",
                "price": "150.00",
                "currency": "INR",
                "data_as_of": "2024-03-09T12:00:00",
                "freshness": "REAL_TIME",
                "provider": "mock",
            }
        ]
    }
    
    # Build prompt
    context = builder.build_context(
        question="What is the current price of RELIANCE.NS?",
        full_context=DashboardResponse.model_validate({
            "period": {"start_date": "2024-03-01", "end_date": "2024-03-08", "period_days": 8},
            "user": {"user_id": 1, "display_name": "Test", "persona": "Professional", "currency": "INR", "country": "IN", "risk_profile": "MODERATE"},
            "summary": {"total_income": "0", "total_expenses": "0", "savings": "0", "net_worth": "0", "total_assets": "0", "total_liabilities": "0", "total_invested": "0", "total_debt": "0"},
            "cash_flow": {"total_income": "0", "total_expenses": "0", "net_cash_flow": "0", "savings": "0", "has_data": False},
            "net_worth": {"total_assets": "0", "total_liabilities": "0", "net_worth": "0", "liquid_assets": "0", "has_data": False},
            "investments": {"total_invested": "0", "current_value": "0", "total_gain_loss": "0", "total_return_percentage": "0", "investment_count": 0, "has_data": False},
            "loans": {"total_outstanding": "0", "total_principal": "0", "total_monthly_emi": "0", "loan_count": 0, "active_loan_count": 0, "has_data": False},
            "debt": {"total_debt": "0", "monthly_obligations": "0", "has_data": False},
            "goals": {"total_goals": 0, "active_count": 0, "completed_count": 0, "has_data": False},
            "budgets": {"total_budget": "0", "total_spending": "0", "remaining_budget": "0", "overall_utilization_percent": "0", "has_data": False},
            "financial_health": {"has_data": False},
        }),
        retrieved_docs=rag_docs,
        live_market_data=live_data,
    )
    prompt = builder.build_prompt(context=context)

    # Verify live data and RAG are formatted, and instructions ask LLM to use Live Market Data as ground truth
    assert "Live Market Data (Authoritative Current Values):" in prompt
    assert '"price": "150.00"' in prompt
    assert "Retrieved General Knowledge:" in prompt
    assert "Stock price is 100" in prompt


@pytest.mark.anyio
async def test_estimated_portfolio_does_not_mutate_db(db_session: Session):
    user = _seed_user(db_session, 987)
    
    # Add a stock investment
    db_session.add(
        Investment(
            user_id=user.id,
            investment_type=InvestmentType.STOCK,
            name="Reliance Share",
            principal=Decimal("2000.00"),
            current_value=Decimal("2000.00"),  # Stored valuation
            quantity=Decimal("1.0"),
            purchase_date=date.today(),
            investment_metadata={"ticker_symbol": "RELIANCE.NS"},
        )
    )
    db_session.commit()

    service = MarketDataService()
    est = await service.calculate_estimated_portfolio(user.id, db_session)
    
    # Stored is 2000, estimated is 2550 (mock price)
    assert est["total_stored_value"] == Decimal("2000.00")
    assert est["total_estimated_value"] == Decimal("2550.00")
    assert est["difference"] == Decimal("550.00")

    # Verify DB record remains unmodified
    db_session.expire_all()
    inv_db = db_session.query(Investment).filter(Investment.user_id == user.id).first()
    assert inv_db.current_value == Decimal("2000.00")


@pytest.mark.anyio
async def test_security_prevents_arbitrary_urls():
    service = MarketDataService()
    
    # Should raise error on URL inputs or scripts
    with pytest.raises(InvalidSymbolError):
        await service.get_stock_quote("http://evil.com/api")

    with pytest.raises(InvalidSymbolError):
        await service.get_stock_quote("RELIANCE; DROP TABLE stock;")
