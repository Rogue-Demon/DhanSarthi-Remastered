"""
Report Enums for DhanSarthi.
"""

from enum import Enum


class ReportType(str, Enum):
    """Supported financial report types."""
    FINANCIAL_SUMMARY = "FINANCIAL_SUMMARY"
    CASH_FLOW = "CASH_FLOW"
    INCOME_EXPENSE = "INCOME_EXPENSE"
    BUDGET = "BUDGET"
    GOALS = "GOALS"
    INVESTMENTS = "INVESTMENTS"
    LIABILITIES = "LIABILITIES"
    MONTHLY_FINANCIAL_REPORT = "MONTHLY_FINANCIAL_REPORT"
    ANNUAL_REPORT = "ANNUAL_REPORT"


class ReportFormat(str, Enum):
    """Supported export formats."""
    PDF = "PDF"
    CSV = "CSV"
    XLSX = "XLSX"
    JSON = "JSON"
