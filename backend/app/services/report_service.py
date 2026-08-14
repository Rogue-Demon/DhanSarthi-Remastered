"""
Report Service for DhanSarthi.

Coordinates financial context fetching via FinancialContextService,
data assembly via ReportDataGenerator, and format rendering via renderers.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Tuple

from sqlalchemy.orm import Session

from app.models.enums import FinancialReportType
from app.reports.generator import ReportDataGenerator, ReportData
from app.reports.renderers.csv_renderer import CSVReportRenderer
from app.reports.renderers.pdf_renderer import PDFReportRenderer
from app.reports.renderers.xlsx_renderer import XLSXReportRenderer
from app.services.financial_context_service import FinancialContextService




ExportFormat = Literal["pdf", "xlsx", "csv"]


class ReportService:
    """Orchestrates financial report generation and format rendering."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.context_service = FinancialContextService(db)

    def generate_report_bytes(
        self,
        user_id: int,
        report_type: FinancialReportType,
        export_format: ExportFormat,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> Tuple[bytes, str, str]:
        """
        Builds user financial context and renders report in requested format.

        Returns:
            Tuple of (file_bytes, media_type, filename)
        """
        # 1. Fetch complete financial context
        context = self.context_service.build_context(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )

        # 2. Build structured ReportData model
        report_data: ReportData = ReportDataGenerator.generate(
            context=context,
            report_type=report_type,
            period_start=date_from,
            period_end=date_to,
        )

        # 3. Render bytes based on format
        fmt = export_format.lower()
        date_str = date_to.isoformat() if date_to else date.today().isoformat()
        filename_prefix = f"dhansarthi_{report_type.value}_{date_str}"

        if fmt == "pdf":
            content = PDFReportRenderer.render(report_data)
            media_type = "application/pdf"
            filename = f"{filename_prefix}.pdf"
        elif fmt == "xlsx":
            content = XLSXReportRenderer.render(report_data)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{filename_prefix}.xlsx"
        elif fmt == "csv":
            content = CSVReportRenderer.render(report_data)
            media_type = "text/csv"
            filename = f"{filename_prefix}.csv"
        else:
            raise ValueError(f"Unsupported export format: '{export_format}'")

        return content, media_type, filename
