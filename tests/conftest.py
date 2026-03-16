from __future__ import annotations

import json
import os
import tempfile

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate

from src.models import ClauseRiskAssessment, ContractReport, ExtractedClause


@pytest.fixture
def sample_clauses() -> list[ExtractedClause]:
    return [
        ExtractedClause(
            clause_type="indemnification",
            clause_text="The Vendor shall indemnify the Client against all claims.",
            page_number=1,
        ),
        ExtractedClause(
            clause_type="termination",
            clause_text="Either party may terminate with 30 days written notice.",
            page_number=2,
        ),
        ExtractedClause(
            clause_type="unclassified",
            clause_text="This agreement is entered into as of the date first written above.",
            page_number=1,
        ),
    ]


@pytest.fixture
def sample_assessments() -> list[ClauseRiskAssessment]:
    return [
        ClauseRiskAssessment(
            clause_type="indemnification",
            clause_text="The Vendor shall indemnify the Client against all claims.",
            risk_level="flag",
            reason="Indemnification is one-sided, only protecting the Client.",
            standard_clause_reference="indemnification",
        ),
        ClauseRiskAssessment(
            clause_type="termination",
            clause_text="Either party may terminate with 30 days written notice.",
            risk_level="ok",
            reason="Standard mutual termination with reasonable notice period.",
            standard_clause_reference="termination",
        ),
        ClauseRiskAssessment(
            clause_type="unclassified",
            clause_text="This agreement is entered into as of the date first written above.",
            risk_level="unclassified",
            reason=None,
            standard_clause_reference=None,
        ),
    ]


@pytest.fixture
def sample_report(sample_assessments: list[ClauseRiskAssessment]) -> ContractReport:
    return ContractReport(
        document_name="test_contract.pdf",
        total_clauses=3,
        executive_summary="The indemnification clause is one-sided and should be negotiated.",
        flagged=[a for a in sample_assessments if a.risk_level == "flag"],
        review=[a for a in sample_assessments if a.risk_level == "review"],
        ok=[a for a in sample_assessments if a.risk_level == "ok"],
        unclassified=[a for a in sample_assessments if a.risk_level == "unclassified"],
    )


@pytest.fixture
def sample_pdf_path() -> str:
    """Create a minimal PDF for testing and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    doc = SimpleDocTemplate(tmp.name, pagesize=A4)
    doc.build([
        Paragraph("This is a test contract. The Vendor shall indemnify the Client against all claims arising from the Vendor's negligence."),
        Paragraph("Either party may terminate this agreement with 30 days written notice."),
        Paragraph("Payment is due within 60 days of invoice date."),
    ])
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def mock_extraction_response() -> str:
    """JSON string mimicking LLM extraction output."""
    return json.dumps([
        {
            "clause_type": "indemnification",
            "clause_text": "The Vendor shall indemnify the Client against all claims arising from the Vendor's negligence.",
            "page_number": 1,
        },
        {
            "clause_type": "termination",
            "clause_text": "Either party may terminate this agreement with 30 days written notice.",
            "page_number": 1,
        },
    ])


@pytest.fixture
def mock_scoring_response() -> str:
    """JSON string mimicking LLM scoring output."""
    return json.dumps({
        "risk_level": "review",
        "reason": "The indemnification clause is one-sided, only protecting the Client.",
    })
