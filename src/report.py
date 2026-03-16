from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.models import ClauseRiskAssessment, ContractReport

# Colour scheme
COLOR_FLAG_BG = colors.Color(0.93, 0.23, 0.23, 0.12)
COLOR_FLAG_BORDER = colors.Color(0.93, 0.23, 0.23, 1)
COLOR_REVIEW_BG = colors.Color(1.0, 0.76, 0.03, 0.12)
COLOR_REVIEW_BORDER = colors.Color(1.0, 0.76, 0.03, 1)
COLOR_OK_BG = colors.Color(0.18, 0.74, 0.36, 0.12)
COLOR_OK_BORDER = colors.Color(0.18, 0.74, 0.36, 1)
COLOR_UNCLASSIFIED_BG = colors.Color(0.6, 0.6, 0.6, 0.12)
COLOR_UNCLASSIFIED_BORDER = colors.Color(0.6, 0.6, 0.6, 1)

RISK_COLORS = {
    "flag": (COLOR_FLAG_BG, COLOR_FLAG_BORDER),
    "review": (COLOR_REVIEW_BG, COLOR_REVIEW_BORDER),
    "ok": (COLOR_OK_BG, COLOR_OK_BORDER),
    "unclassified": (COLOR_UNCLASSIFIED_BG, COLOR_UNCLASSIFIED_BORDER),
}


def generate_report(report: ContractReport) -> bytes:
    """Render a ContractReport as a colour-coded PDF. Returns PDF bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontSize=18, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey
    )
    section_style = ParagraphStyle(
        "SectionHeader", parent=styles["Heading2"], fontSize=14, spaceBefore=12, spaceAfter=6
    )
    body_style = ParagraphStyle(
        "ClauseBody", parent=styles["Normal"], fontSize=9, leading=12
    )
    label_style = ParagraphStyle(
        "ClauseLabel", parent=styles["Normal"], fontSize=9, textColor=colors.grey
    )

    elements: list = []

    # Title
    elements.append(Paragraph(f"Contract Risk Report: {report.document_name}", title_style))
    elements.append(Paragraph(f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 6 * mm))

    # Counts
    counts_text = (
        f"Total clauses: {report.total_clauses} &nbsp;|&nbsp; "
        f"<font color='red'><b>Flagged: {len(report.flagged)}</b></font> &nbsp;|&nbsp; "
        f"<font color='#C4A000'><b>Review: {len(report.review)}</b></font> &nbsp;|&nbsp; "
        f"<font color='green'><b>OK: {len(report.ok)}</b></font> &nbsp;|&nbsp; "
        f"Unclassified: {len(report.unclassified)}"
    )
    elements.append(Paragraph(counts_text, styles["Normal"]))
    elements.append(Spacer(1, 6 * mm))

    # Executive summary
    summary_style = ParagraphStyle(
        "ExecutiveSummary", parent=styles["Normal"], fontSize=10, leading=14,
        spaceBefore=4, spaceAfter=4, leftIndent=8, rightIndent=8,
    )
    elements.append(Paragraph("<b>Executive Summary</b>", section_style))
    elements.append(Paragraph(_escape(report.executive_summary), summary_style))
    elements.append(Spacer(1, 6 * mm))

    # Sections in risk order
    sections = [
        ("Flagged Clauses", report.flagged, "flag"),
        ("Clauses for Review", report.review, "review"),
        ("Passed Clauses", report.ok, "ok"),
        ("Unclassified Clauses", report.unclassified, "unclassified"),
    ]

    for section_title, clauses, risk_key in sections:
        if not clauses:
            continue

        elements.append(Paragraph(section_title, section_style))

        for clause in clauses:
            card = _build_clause_card(clause, risk_key, body_style, label_style)
            elements.append(card)
            elements.append(Spacer(1, 4 * mm))

    doc.build(elements)
    return buffer.getvalue()


def _build_clause_card(
    clause: ClauseRiskAssessment,
    risk_key: str,
    body_style: ParagraphStyle,
    label_style: ParagraphStyle,
) -> Table:
    """Build a coloured card table for a single clause."""
    bg_color, border_color = RISK_COLORS[risk_key]

    rows = []

    # Row 1: type + risk label
    type_label = clause.clause_type.title()
    risk_label = clause.risk_level.upper()
    rows.append([Paragraph(f"<b>{type_label}</b> — {risk_label}", body_style)])

    # Row 2: clause text
    rows.append([Paragraph(f"<i>Contract clause:</i><br/>{_escape(clause.clause_text)}", body_style)])

    # Row 3: standard clause (if available)
    if clause.standard_clause_reference:
        rows.append([Paragraph(f"<i>Matched standard:</i> {_escape(clause.standard_clause_reference)}", label_style)])

    # Row 4: reason (if available)
    if clause.reason:
        rows.append([Paragraph(f"<i>Risk assessment:</i> {_escape(clause.reason)}", body_style)])

    page_width = A4[0] - 30 * mm  # account for margins
    table = Table(rows, colWidths=[page_width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("LINEBELOW", (0, 0), (-1, 0), 1, border_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _escape(text: str) -> str:
    """Escape XML special characters for ReportLab paragraphs."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
