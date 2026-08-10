"""
DhanSarthi Financial Engine Package.

The Financial Engine is the pure, deterministic numerical calculation layer of
DhanSarthi. It performs monetary arithmetic using ``decimal.Decimal`` independently
of FastAPI, PostgreSQL, LLMs, and external APIs.
"""

from app.financial.budget import analyze_budget
from app.financial.cash_flow import calculate_cash_flow
from app.financial.debt import analyze_debt
from app.financial.exceptions import (
    FinancialEngineError,
    InsufficientFinancialData,
    InvalidCalculationPeriod,
    InvalidFinancialInput,
    InvalidInvestmentParameters,
    InvalidLoanParameters,
)
from app.financial.goals import analyze_goal
from app.financial.health import (
    calculate_emergency_fund_coverage,
    calculate_financial_metrics,
)
from app.financial.investments import (
    analyze_portfolio,
    calculate_compounding,
    calculate_investment_return,
    calculate_sip,
)
from app.financial.loans import analyze_loan_affordability, calculate_loan
from app.financial.net_worth import calculate_net_worth
from app.financial.savings import calculate_savings
from app.financial.types import (
    AmortizationScheduleEntry,
    AssetItemInput,
    BudgetAnalysisInput,
    BudgetAnalysisResult,
    BudgetCategoryInput,
    BudgetCategoryResult,
    CashFlowInput,
    CashFlowResult,
    CompoundingInput,
    CompoundingResult,
    DebtAnalysisResult,
    ExpenseItemInput,
    FinancialMetricsInput,
    FinancialMetricsResult,
    GoalAnalysisResult,
    GoalInput,
    IncomeItemInput,
    InvestmentItemInput,
    InvestmentReturnResult,
    LiabilityItemInput,
    LoanAffordabilityInput,
    LoanAffordabilityResult,
    LoanCalculationResult,
    LoanInput,
    NetWorthInput,
    NetWorthResult,
    PortfolioInput,
    PortfolioSummaryResult,
    SIPCalculationResult,
    SIPInput,
    SavingsResult,
)

__all__ = [
    # Exceptions
    "FinancialEngineError",
    "InvalidFinancialInput",
    "InvalidLoanParameters",
    "InvalidInvestmentParameters",
    "InsufficientFinancialData",
    "InvalidCalculationPeriod",
    # Input Types
    "IncomeItemInput",
    "ExpenseItemInput",
    "CashFlowInput",
    "AssetItemInput",
    "LiabilityItemInput",
    "NetWorthInput",
    "LoanInput",
    "LoanAffordabilityInput",
    "SIPInput",
    "CompoundingInput",
    "InvestmentItemInput",
    "PortfolioInput",
    "GoalInput",
    "BudgetCategoryInput",
    "BudgetAnalysisInput",
    "FinancialMetricsInput",
    # Result Types
    "CashFlowResult",
    "SavingsResult",
    "NetWorthResult",
    "DebtAnalysisResult",
    "AmortizationScheduleEntry",
    "LoanCalculationResult",
    "LoanAffordabilityResult",
    "SIPCalculationResult",
    "CompoundingResult",
    "InvestmentReturnResult",
    "PortfolioSummaryResult",
    "GoalAnalysisResult",
    "BudgetCategoryResult",
    "BudgetAnalysisResult",
    "FinancialMetricsResult",
    # Functions
    "calculate_cash_flow",
    "calculate_savings",
    "calculate_net_worth",
    "analyze_debt",
    "calculate_loan",
    "analyze_loan_affordability",
    "calculate_compounding",
    "calculate_sip",
    "calculate_investment_return",
    "analyze_portfolio",
    "analyze_goal",
    "analyze_budget",
    "calculate_emergency_fund_coverage",
    "calculate_financial_metrics",
]
