from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from src.clients import build_embeddings
from src.models import ExtractedClause
from src.retriever import find_standard_match


@pytest.fixture
def temp_vectorstore():
    """Build a small test vectorstore in a temp directory."""
    from langchain_community.vectorstores import Chroma

    tmpdir = tempfile.mkdtemp()
    embeddings = build_embeddings()

    texts = [
        "Each party shall indemnify the other against third-party claims.",
        "Either party may terminate with 30 days notice.",
    ]
    metadatas = [
        {"clause_type": "indemnification"},
        {"clause_type": "termination"},
    ]

    vs = Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=embeddings,
        persist_directory=tmpdir,
        collection_name="test_clauses",
    )
    yield vs
    # ChromaDB may hold file locks on Windows; ignore cleanup errors
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_find_standard_match(temp_vectorstore):
    clause = ExtractedClause(
        clause_type="indemnification",
        clause_text="The Vendor shall indemnify the Client against all losses.",
        page_number=1,
    )
    text, label = find_standard_match(clause, temp_vectorstore)
    assert len(text) > 0
    assert label in ("indemnification", "termination")
