from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.models import ContractReport
from src.pipeline import run_pipeline


def test_run_pipeline_end_to_end(sample_pdf_path):
    """End-to-end test with all LLM calls mocked."""
    mock_extraction = [
        {
            "clause_type": "indemnification",
            "clause_text": "The Vendor shall indemnify the Client.",
            "page_number": 1,
        },
    ]
    mock_scoring = {
        "risk_level": "flag",
        "reason": "One-sided indemnification clause.",
    }

    stages_called = []

    def on_stage(stage: int, label: str) -> None:
        stages_called.append(stage)

    with patch("src.pipeline.build_llm") as mock_build_llm, \
         patch("src.pipeline.build_embeddings") as mock_build_emb, \
         patch("src.pipeline.extract_clauses") as mock_extract, \
         patch("src.pipeline.get_vectorstore") as mock_get_vs, \
         patch("src.pipeline.score_clauses") as mock_score, \
         patch("src.pipeline.generate_executive_summary") as mock_summary:

        from src.models import ClauseRiskAssessment, ExtractedClause

        mock_extract.return_value = [
            ExtractedClause(**mock_extraction[0]),
        ]
        mock_score.return_value = [
            ClauseRiskAssessment(
                clause_type="indemnification",
                clause_text="The Vendor shall indemnify the Client.",
                risk_level="flag",
                reason="One-sided indemnification clause.",
                standard_clause_reference="indemnification",
            ),
        ]
        mock_summary.return_value = "The indemnification clause is one-sided."

        report, pdf_bytes = run_pipeline(sample_pdf_path, on_stage=on_stage)

    assert isinstance(report, ContractReport)
    assert report.total_clauses == 1
    assert len(report.flagged) == 1
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:5] == b"%PDF-"
    assert stages_called == [1, 2, 3, 4, 5]
