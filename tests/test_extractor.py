from __future__ import annotations

import json
from unittest.mock import MagicMock

from langchain_community.chat_models.fake import FakeListChatModel

from src.extractor import extract_clauses
from src.models import ExtractedClause


def test_extract_clauses_from_chunks():
    mock_response = [
        {
            "clause_type": "indemnification",
            "clause_text": "The Vendor shall indemnify the Client.",
            "page_number": 1,
        },
        {
            "clause_type": "termination",
            "clause_text": "Either party may terminate with 30 days notice.",
            "page_number": 1,
        },
    ]

    fake_llm = FakeListChatModel(responses=[json.dumps(mock_response)])

    mock_chunk = MagicMock()
    mock_chunk.page_content = "Test contract text..."
    mock_chunk.metadata = {"page": 0}

    clauses = extract_clauses([mock_chunk], fake_llm)

    assert len(clauses) == 2
    assert all(isinstance(c, ExtractedClause) for c in clauses)
    assert clauses[0].clause_type == "indemnification"
    assert clauses[1].clause_type == "termination"


def test_extract_clauses_empty_chunk():
    fake_llm = FakeListChatModel(responses=[json.dumps([])])

    mock_chunk = MagicMock()
    mock_chunk.page_content = "No legal clauses here."
    mock_chunk.metadata = {"page": 0}

    clauses = extract_clauses([mock_chunk], fake_llm)
    assert len(clauses) == 0
