"""Financial Engine API router for DhanSarthi.

Exposes deterministic financial calculations and user-scoped financial
summaries powered by the Financial Engine. No AI, no natural-language advice.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_id, get_financial_service
from app.financial import (
    GoalInput,
    LoanInput,
    SIPInput,
    analyze_goal,
    calculate_loan,
    calculate_sip,
)
from app.schemas.financial import (
    FinancialSummaryResponse,
    LoanCalculateRequest,
    SIPCalculateRequest,
)
from app.services.financial_service import FinancialService

router = APIRouter(prefix="/financial", tags=["financial"])


# ============================================================================
# Financial Summary
# ============================================================================


@router.get("/summary", response_model=FinancialSummaryResponse)
def get_financial_summary(
    user_id: int = Depends(get_current_user_id),
    service: FinancialService = Depends(get_financial_service),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
) -> FinancialSummaryResponse:
    """Return consolidated financial summary for the current user."""
    cf = service.get_user_cash_flow(user_id, date_from=date_from, date_to=date_to)
    from app.financial import calculate_savings

    sav = calculate_savings(cf.total_income, cf.total_expenses)
    nw = service.get_user_net_worth(user_id)

    return FinancialSummaryResponse(
        total_income=cf.total_income,
        total_expenses=cf.total_expenses,
        savings=sav.savings,
        savings_rate_percent=sav.savings_rate_percent,
        total_assets=nw.total_assets,
        total_liabilities=nw.total_liabilities,
        net_worth=nw.net_worth,
    )


# ============================================================================
# Cash Flow
# ============================================================================


@router.get("/cash-flow")
def get_cash_flow(
    user_id: int = Depends(get_current_user_id),
    service: FinancialService = Depends(get_financial_service),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
) -> dict:
    """Return cash flow analysis for the current user."""
    result = service.get_user_cash_flow(user_id, date_from=date_from, date_to=date_to)
    return result.model_dump(mode="json")


# ============================================================================
# Savings
# ============================================================================


@router.get("/savings")
def get_savings(
    user_id: int = Depends(get_current_user_id),
    service: FinancialService = Depends(get_financial_service),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
) -> dict:
    """Return savings analysis for the current user."""
    result = service.get_user_savings(user_id, date_from=date_from, date_to=date_to)
    return result.model_dump(mode="json")


# ============================================================================
# Net Worth
# ============================================================================


@router.get("/net-worth")
def get_net_worth(
    user_id: int = Depends(get_current_user_id),
    service: FinancialService = Depends(get_financial_service),
) -> dict:
    """Return net worth breakdown for the current user."""
    result = service.get_user_net_worth(user_id)
    return result.model_dump(mode="json")


# ============================================================================
# Debt Analysis
# ============================================================================


@router.get("/debt")
def get_debt_analysis(
    user_id: int = Depends(get_current_user_id),
    service: FinancialService = Depends(get_financial_service),
) -> dict:
    """Return debt metrics and DTI ratio for the current user."""
    result = service.get_user_debt_analysis(user_id)
    return result.model_dump(mode="json")


# ============================================================================
# Investment Summary
# ============================================================================


@router.get("/investments/summary")
def get_investment_summary(
    user_id: int = Depends(get_current_user_id),
    service: FinancialService = Depends(get_financial_service),
) -> dict:
    """Return portfolio summary for the current user's investments."""
    result = service.get_user_portfolio_summary(user_id)
    return result.model_dump(mode="json")


# ============================================================================
# Loan Calculation (Pure — no DB record created)
# ============================================================================


@router.post("/loan/calculate")
def calculate_loan_endpoint(data: LoanCalculateRequest) -> dict:
    """Calculate EMI, total interest, and amortization for given loan parameters.

    This is a pure calculation endpoint — no Loan record is created in the database.
    """
    loan_input = LoanInput(
        principal=data.principal,
        annual_interest_rate_percent=data.annual_interest_rate_percent,
        tenure_months=data.tenure_months,
        payment_frequency=data.payment_frequency,
    )
    result = calculate_loan(loan_input, include_amortization=True)
    return result.model_dump(mode="json")


# ============================================================================
# SIP Calculation (Pure — no DB record created)
# ============================================================================


@router.post("/investments/sip/calculate")
def calculate_sip_endpoint(data: SIPCalculateRequest) -> dict:
    """Project SIP future value and gains for given contribution parameters.

    This is a pure calculation endpoint with explicitly stated assumptions.
    """
    sip_input = SIPInput(
        monthly_contribution=data.monthly_contribution,
        expected_annual_return_percent=data.expected_annual_return_percent,
        duration_years=data.duration_years,
        contribution_frequency=data.contribution_frequency,
    )
    result = calculate_sip(sip_input)
    return result.model_dump(mode="json")


# ============================================================================
# Budget Summary (Financial Engine powered)
# ============================================================================


@router.get("/budget")
def get_budget_summary(
    user_id: int = Depends(get_current_user_id),
    service: FinancialService = Depends(get_financial_service),
) -> dict:
    """Return budget utilization analysis for the current user."""
    result = service.get_user_budget_analysis(user_id)
    return result.model_dump(mode="json")


# ============================================================================
# Goal Summary (Financial Engine powered)
# ============================================================================


@router.get("/goals")
def get_goal_summaries(
    user_id: int = Depends(get_current_user_id),
    service: FinancialService = Depends(get_financial_service),
) -> list[dict]:
    """Return goal analysis for each of the current user's goals."""
    from app.repositories.goal_repository import GoalRepository
    from app.core.database import get_db

    # Access the goal repository through the financial service's internal db session
    goal_repo = GoalRepository(service._db)
    goals = goal_repo.list_for_user(user_id)

    results = []
    for goal in goals:
        goal_input = GoalInput(
            title=goal.title,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=goal.target_date,
        )
        analysis = analyze_goal(goal_input)
        results.append(analysis.model_dump(mode="json"))
    return results
