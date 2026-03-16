from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ExtractedClause(BaseModel):
    clause_type: str  # known type or "unclassified"
    clause_text: str
    page_number: int


class ClauseRiskAssessment(BaseModel):
    clause_type: str
    clause_text: str
    risk_level: Literal["ok", "review", "flag", "unclassified"]
    reason: str | None = None  # None for unclassified clauses
    standard_clause_reference: str | None = None  # None for unclassified clauses


class ContractReport(BaseModel):
    document_name: str
    total_clauses: int
    executive_summary: str
    flagged: list[ClauseRiskAssessment]
    review: list[ClauseRiskAssessment]
    ok: list[ClauseRiskAssessment]
    unclassified: list[ClauseRiskAssessment]
