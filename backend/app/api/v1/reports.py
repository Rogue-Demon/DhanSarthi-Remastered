"""
FastAPI router for DhanSarthi Financial Reports.

Exposes endpoints to generate and download formatted financial statement exports
(PDF, Excel XLSX, and CSV).
All endpoints require valid JWT authentication.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import Response

from app.api.deps import get_current_user_id, get_report_service
from app.reports.generator import FinancialReportType
from app.services.report_service import ReportService



router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/export",
    summary="Export financial statement report",
    description=(
        "Generates a styled financial statement report in PDF, Excel (.xlsx), or CSV format. "
        "Content is custom-tailored using the user's live financial engine data."
    ),
    response_class=Response,
)
def export_report(
    report_type: FinancialReportType = Query(
        default=FinancialReportType.MONTHLY_EXECUTIVE,
        description="Type of report (monthly_executive, annual_tax_summary, expense_breakdown, net_worth_statement, goal_feasibility, debt_snowball)"
    ),
    format: Literal["pdf", "xlsx", "csv"] = Query(
        default="pdf",
        description="Target file format (pdf, xlsx, csv)"
    ),
    date_from: Optional[date] = Query(
        default=None,
        description="Start date of reporting period (YYYY-MM-DD)"
    ),
    date_to: Optional[date] = Query(
        default=None,
        description="End date of reporting period (YYYY-MM-DD)"
    ),
    user_id: int = Depends(get_current_user_id),
    report_service: ReportService = Depends(get_report_service),
) -> Response:
    """
    Generates and streams financial report bytes.
    """
    file_bytes, media_type, filename = report_service.generate_report_bytes(
        user_id=user_id,
        report_type=report_type,
        export_format=format,
        date_from=date_from,
        date_to=date_to,
    )

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
