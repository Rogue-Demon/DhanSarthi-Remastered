"""
Financial Intelligence and Decision Engine.
"""

from app.financial_intelligence.schemas import (
    FinancialInsight,
    FinancialIntelligenceSummary,
    LoanScenarioInput,
    LoanScenarioResult,
    GenericScenarioInput,
    GenericScenarioResult,
)
from app.financial_intelligence.analyzers.cash_flow import analyze_cash_flow, analyze_savings
from app.financial_intelligence.analyzers.expenses import analyze_expenses
from app.financial_intelligence.analyzers.budget import analyze_budget
from app.financial_intelligence.analyzers.debt import analyze_debt_burden
from app.financial_intelligence.analyzers.emergency_fund import analyze_emergency_fund
from app.financial_intelligence.analyzers.investments import analyze_investments
from app.financial_intelligence.analyzers.goals import analyze_goals

from app.financial_intelligence.scenarios.engine import (
    calculate_emi,
    run_loan_scenario,
    run_savings_scenario,
    run_investment_scenario,
    run_goal_scenario,
)

from app.financial_intelligence.rules.engine import (
    evaluate_warnings,
    evaluate_opportunities,
)
