"""
Pydantic schemas for DhanSarthi Financial Reports.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field

from app.reports.generator import FinancialReportType



class ReportExportRequest(BaseModel):
    """Query/Body parameters for exporting a financial report."""

    report_type: FinancialReportType = Field(
        default=FinancialReportType.MONTHLY_EXECUTIVE,
        description="Type of report to generate (monthly_executive, annual_tax_summary, expense_breakdown, net_worth_statement, goal_feasibility, debt_snowball)."
    )
    format: Literal["pdf", "xlsx", "csv"] = Field(
        default="pdf",
        description="Export file format: pdf, xlsx, or csv."
    )
    date_from: Optional[date] = Field(
        default=None,
        description="Start date for reporting period (defaults to 30 days ago)."
    )
    date_to: Optional[date] = Field(
        default=None,
        description="End date for reporting period (defaults to today)."
    )
