from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from langchain_community.chat_models.fake import FakeListChatModel

from src.models import ClauseRiskAssessment, ExtractedClause
from src.scorer import score_clauses


def test_score_classified_clause():
    mock_vectorstore = MagicMock()

    clause = ExtractedClause(
        clause_type="indemnification",
        clause_text="The Vendor shall indemnify the Client.",
        page_number=1,
    )

    scoring_result = json.dumps({
        "risk_level": "flag",
        "reason": "One-sided indemnification.",
    })
    fake_llm = FakeListChatModel(responses=[scoring_result])

    with patch("src.scorer.find_standard_match") as mock_find:
        mock_find.return_value = ("Standard indemnification clause text.", "indemnification")
        assessments = score_clauses([clause], fake_llm, mock_vectorstore)

    assert len(assessments) == 1
    assert assessments[0].risk_level == "flag"
    assert assessments[0].standard_clause_reference == "indemnification"


def test_score_unclassified_clause():
    mock_vectorstore = MagicMock()

    clause = ExtractedClause(
        clause_type="unclassified",
        clause_text="This agreement is made on this day.",
        page_number=1,
    )

    scoring_result = json.dumps({
        "risk_level": "ok",
        "reason": "Standard boilerplate with no risk.",
    })
    fake_llm = FakeListChatModel(responses=[scoring_result])

    assessments = score_clauses([clause], fake_llm, mock_vectorstore)

    assert len(assessments) == 1
    assert assessments[0].risk_level == "ok"
    assert assessments[0].reason == "Standard boilerplate with no risk."
    assert assessments[0].standard_clause_reference is None
