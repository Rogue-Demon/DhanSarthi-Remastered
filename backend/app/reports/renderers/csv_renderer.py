"""
CSV Report Renderer for DhanSarthi.
Generates UTF-8 encoded RFC 4180 compliant CSV exports with proper section headers and escaped values.
"""

from __future__ import annotations

import csv
import io
from app.reports.generator import ReportData


class CSVReportRenderer:
    """Renders structured ReportData to a CSV string."""

    @staticmethod
    def render(data: ReportData) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header metadata
        writer.writerow(["DhanSarthi Financial Report", data.title])
        writer.writerow(["User", data.user_name, data.user_email])
        writer.writerow(["Period", f"{data.period_start} to {data.period_end}"])
        writer.writerow(["Generated At", data.generated_at])
        writer.writerow(["Data Freshness", data.data_freshness])
        writer.writerow([])

        # Summary KPIs
        if data.summary_kpis:
            writer.writerow(["--- Executive KPI Summary ---"])
            writer.writerow(["Metric", "Value", "Notes"])
            for kpi in data.summary_kpis:
                writer.writerow([kpi.label, kpi.value, kpi.subtext or ""])
            writer.writerow([])

        # Tables
        for table in data.tables:
            writer.writerow([f"--- {table.title} ---"])
            writer.writerow(table.headers)
            for row in table.rows:
                writer.writerow(row)
            if table.totals:
                writer.writerow(table.totals)
            writer.writerow([])

        # Footnotes
        if data.footnotes:
            writer.writerow(["--- Disclaimers & Notes ---"])
            for note in data.footnotes:
                writer.writerow([note])

        return output.getvalue().encode("utf-8")
