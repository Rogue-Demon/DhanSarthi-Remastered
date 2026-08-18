"""
PDF Report Renderer for DhanSarthi.

Generates styled PDF financial statements using reportlab.
Falls back to a plain-text layout if reportlab is not installed
(graceful degradation rather than import crash).
"""

from __future__ import annotations

import io
from typing import Optional

from app.reports.generator import ReportData


class PDFReportRenderer:
    """Renders structured ReportData into a well-formatted PDF byte stream."""

    @staticmethod
    def render(data: ReportData) -> bytes:
        try:
            return PDFReportRenderer._render_with_reportlab(data)
        except ImportError:
            return PDFReportRenderer._render_plaintext_fallback(data)

    # ------------------------------------------------------------------
    # reportlab-based renderer
    # ------------------------------------------------------------------
    @staticmethod
    def _render_with_reportlab(data: ReportData) -> bytes:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()
        # Custom styles
        title_style = ParagraphStyle(
            "DSTitle",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0D9488"),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "DSSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=12,
        )
        section_style = ParagraphStyle(
            "DSSection",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=6,
        )
        footnote_style = ParagraphStyle(
            "DSFootnote",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#94A3B8"),
            spaceBefore=10,
        )

        elements = []

        # Title & metadata
        elements.append(Paragraph("DhanSarthi Financial Statement", title_style))
        elements.append(Paragraph(data.title, section_style))
        meta_lines = [
            f"<b>Account Holder:</b> {data.user_name} ({data.user_email})",
            f"<b>Period:</b> {data.period_start} to {data.period_end}",
            f"<b>Generated:</b> {data.generated_at}",
            f"<b>Data Freshness:</b> {data.data_freshness}",
        ]
        for line in meta_lines:
            elements.append(Paragraph(line, subtitle_style))
        elements.append(Spacer(1, 8))

        # --- KPI Summary Table ---
        if data.summary_kpis:
            elements.append(Paragraph("Executive KPI Summary", section_style))
            kpi_data = [["Metric", "Value", "Context"]]
            for kpi in data.summary_kpis:
                kpi_data.append([kpi.label, kpi.value, kpi.subtext or ""])

            kpi_table = Table(kpi_data, hAlign="LEFT", repeatRows=1)
            kpi_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D9488")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]))
            elements.append(kpi_table)
            elements.append(Spacer(1, 12))

        # --- Data Tables ---
        for table in data.tables:
            elements.append(Paragraph(table.title, section_style))
            table_data = [table.headers]
            for row in table.rows:
                table_data.append([str(c) for c in row])
            if table.totals:
                table_data.append([str(c) for c in table.totals])

            pdf_table = Table(table_data, hAlign="LEFT", repeatRows=1)

            style_commands = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D9488")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
            if table.totals:
                last_row = len(table_data) - 1
                style_commands.extend([
                    ("FONTNAME", (0, last_row), (-1, last_row), "Helvetica-Bold"),
                    ("LINEABOVE", (0, last_row), (-1, last_row), 1, colors.HexColor("#0F172A")),
                ])

            pdf_table.setStyle(TableStyle(style_commands))
            elements.append(pdf_table)
            elements.append(Spacer(1, 10))

        # --- Footnotes ---
        if data.footnotes:
            elements.append(Spacer(1, 6))
            for note in data.footnotes:
                elements.append(Paragraph(f"• {note}", footnote_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # Plain-text fallback (if reportlab is not installed)
    # ------------------------------------------------------------------
    @staticmethod
    def _render_plaintext_fallback(data: ReportData) -> bytes:
        lines = []
        lines.append("=" * 72)
        lines.append(f"  DhanSarthi Financial Statement — {data.title}")
        lines.append("=" * 72)
        lines.append(f"  Account Holder: {data.user_name} ({data.user_email})")
        lines.append(f"  Period: {data.period_start} to {data.period_end}")
        lines.append(f"  Generated: {data.generated_at}")
        lines.append(f"  Data Freshness: {data.data_freshness}")
        lines.append("")

        if data.summary_kpis:
            lines.append("-" * 40)
            lines.append("  Executive KPI Summary")
            lines.append("-" * 40)
            for kpi in data.summary_kpis:
                lines.append(f"  {kpi.label}: {kpi.value}")
            lines.append("")

        for table in data.tables:
            lines.append("-" * 40)
            lines.append(f"  {table.title}")
            lines.append("-" * 40)
            lines.append("  " + " | ".join(table.headers))
            for row in table.rows:
                lines.append("  " + " | ".join(str(c) for c in row))
            if table.totals:
                lines.append("  " + " | ".join(str(c) for c in table.totals))
            lines.append("")

        if data.footnotes:
            for note in data.footnotes:
                lines.append(f"  * {note}")

        return "\n".join(lines).encode("utf-8")
