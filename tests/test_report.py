from __future__ import annotations

from src.models import ContractReport
from src.report import generate_report


def test_generate_report_returns_pdf_bytes(sample_report):
    pdf_bytes = generate_report(sample_report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF files start with %PDF
    assert pdf_bytes[:5] == b"%PDF-"


def test_generate_report_empty_sections():
    report = ContractReport(
        document_name="empty_contract.pdf",
        total_clauses=0,
        executive_summary="No significant risks were identified in this contract.",
        flagged=[],
        review=[],
        ok=[],
        unclassified=[],
    )
    pdf_bytes = generate_report(report)
    assert pdf_bytes[:5] == b"%PDF-"
