from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import ClauseRiskAssessment, ContractReport, ExtractedClause


def test_extracted_clause_valid():
    clause = ExtractedClause(
        clause_type="indemnification",
        clause_text="Test clause text",
        page_number=1,
    )
    assert clause.clause_type == "indemnification"
    assert clause.page_number == 1


def test_extracted_clause_missing_field():
    with pytest.raises(ValidationError):
        ExtractedClause(clause_type="indemnification", clause_text="Test")


def test_clause_risk_assessment_unclassified():
    assessment = ClauseRiskAssessment(
        clause_type="unclassified",
        clause_text="Boilerplate text",
        risk_level="unclassified",
    )
    assert assessment.reason is None
    assert assessment.standard_clause_reference is None


def test_clause_risk_assessment_valid_levels():
    for level in ("ok", "review", "flag", "unclassified"):
        a = ClauseRiskAssessment(
            clause_type="termination",
            clause_text="Test",
            risk_level=level,
        )
        assert a.risk_level == level


def test_clause_risk_assessment_invalid_level():
    with pytest.raises(ValidationError):
        ClauseRiskAssessment(
            clause_type="termination",
            clause_text="Test",
            risk_level="invalid",
        )


def test_contract_report(sample_report):
    assert sample_report.total_clauses == 3
    assert len(sample_report.flagged) == 1
    assert len(sample_report.ok) == 1
    assert len(sample_report.unclassified) == 1
