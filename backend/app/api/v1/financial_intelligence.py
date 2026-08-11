"""
REST API Router for DhanSarthi Financial Intelligence and Decision Engine.
"""

from __future__ import annotations

from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_financial_intelligence_service
from app.services.financial_intelligence_service import FinancialIntelligenceService
from app.financial_intelligence.schemas import (
    FinancialInsight,
    FinancialIntelligenceSummary,
    LoanScenarioInput,
    LoanScenarioResult,
    GenericScenarioInput,
    GenericScenarioResult,
)

router = APIRouter(
    prefix="/financial-intelligence",
    tags=["Financial Intelligence"],
)


@router.get(
    "/summary",
    response_model=FinancialIntelligenceSummary,
    summary="Get consolidated financial summary",
)
def get_summary(
    user_id: int = Depends(get_current_user_id),
    date_from: date | None = Query(default=None, description="Start date of calculation window"),
    date_to: date | None = Query(default=None, description="End date of calculation window"),
    intel_svc: FinancialIntelligenceService = Depends(get_financial_intelligence_service),
) -> FinancialIntelligenceSummary:
    """
    Get consolidated financial summary including cash flow, net worth, investments, goals, warnings, and opportunities.
    """
    return intel_svc.build_summary(user_id=user_id, date_from=date_from, date_to=date_to)


@router.get(
    "/cash-flow",
    response_model=FinancialInsight,
    summary="Get cash flow analysis",
)
def get_cash_flow(
    user_id: int = Depends(get_current_user_id),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    intel_svc: FinancialIntelligenceService = Depends(get_financial_intelligence_service),
) -> FinancialInsight:
    """
    Retrieve structured net cash flow analysis for the user.
    """
    summary = intel_svc.build_summary(user_id=user_id, date_from=date_from, date_to=date_to)
    return summary.cash_flow


@router.get(
    "/debt",
    response_model=FinancialInsight,
    summary="Get debt analysis",
)
def get_debt(
    user_id: int = Depends(get_current_user_id),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    intel_svc: FinancialIntelligenceService = Depends(get_financial_intelligence_service),
) -> FinancialInsight:
    """
    Retrieve structured DTI and liability analysis.
    """
    summary = intel_svc.build_summary(user_id=user_id, date_from=date_from, date_to=date_to)
    return summary.debt


@router.get(
    "/investments",
    response_model=FinancialInsight,
    summary="Get investment analysis",
)
def get_investments(
    user_id: int = Depends(get_current_user_id),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    intel_svc: FinancialIntelligenceService = Depends(get_financial_intelligence_service),
) -> FinancialInsight:
    """
    Retrieve structured portfolio allocation, performance, and concentration analysis.
    """
    summary = intel_svc.build_summary(user_id=user_id, date_from=date_from, date_to=date_to)
    return summary.investments


@router.get(
    "/goals",
    response_model=List[FinancialInsight],
    summary="Get goals feasibility analysis",
)
def get_goals(
    user_id: int = Depends(get_current_user_id),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    intel_svc: FinancialIntelligenceService = Depends(get_financial_intelligence_service),
) -> List[FinancialInsight]:
    """
    Retrieve per-goal feasibility and shortfall analysis list.
    """
    summary = intel_svc.build_summary(user_id=user_id, date_from=date_from, date_to=date_to)
    return summary.goals


@router.post(
    "/loan-scenario",
    response_model=LoanScenarioResult,
    summary="Evaluate proposed loan affordability",
)
def evaluate_loan(
    req: LoanScenarioInput,
    user_id: int = Depends(get_current_user_id),
    intel_svc: FinancialIntelligenceService = Depends(get_financial_intelligence_service),
) -> LoanScenarioResult:
    """
    Simulate standard EMI payments, total interest, post-loan DTI, and cash flow risk flags.
    """
    return intel_svc.run_loan_scenario(
        user_id=user_id,
        principal=req.principal,
        annual_interest_rate_percent=req.annual_interest_rate_percent,
        tenure_months=req.tenure_months,
    )


@router.post(
    "/scenario",
    response_model=GenericScenarioResult,
    summary="Evaluate generic savings or compounding SIP scenario",
)
def evaluate_scenario(
    req: GenericScenarioInput,
    user_id: int = Depends(get_current_user_id),
    intel_svc: FinancialIntelligenceService = Depends(get_financial_intelligence_service),
) -> GenericScenarioResult:
    """
    Evaluate savings, compounding, or SIP growth scenario comparisons.
    """
    from decimal import Decimal
    
    stype = req.scenario_type.upper()
    if stype == "SAVINGS":
        expense_reduction = Decimal(str(req.params.get("expense_reduction", 0)))
        return intel_svc.run_savings_scenario(user_id=user_id, expense_reduction=expense_reduction)
    elif stype == "INVESTMENT_GROWTH":
        monthly = Decimal(str(req.params.get("monthly_contribution", 0)))
        rate = Decimal(str(req.params.get("expected_annual_return_percent", 0)))
        years = Decimal(str(req.params.get("duration_years", 0)))
        return intel_svc.run_investment_scenario(
            user_id=user_id,
            monthly_contribution=monthly,
            expected_annual_return_percent=rate,
            duration_years=years,
        )
    elif stype == "GOAL_CONTRIBUTION":
        goal_id = int(req.params.get("goal_id", 0))
        proposed = Decimal(str(req.params.get("proposed_monthly_contribution", 0)))
        return intel_svc.run_goal_scenario(
            user_id=user_id,
            goal_id=goal_id,
            proposed_monthly_contribution=proposed,
        )
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported scenario type: {req.scenario_type}",
        )
