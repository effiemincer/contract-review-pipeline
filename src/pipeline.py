from __future__ import annotations

from collections import Counter
from typing import BinaryIO, Callable

from src.clients import build_embeddings, build_llm
from src.extractor import extract_clauses
from src.loader import load_and_chunk
from src.models import ContractReport
from src.report import generate_report
from src.retriever import get_vectorstore
from src.scorer import generate_executive_summary, score_clauses

STAGES = [
    "Loading PDF and splitting into chunks",
    "Extracting and classifying clauses",
    "Comparing clauses against standard terms",
    "Scoring risk for each clause",
    "Generating report",
]


def run_pipeline(
    source: str | BinaryIO,
    on_stage: Callable[[int, str], None] | None = None,
) -> tuple[ContractReport, bytes]:
    """Run the full 5-stage contract review pipeline.

    Args:
        source: File path (str) or file-like object (BytesIO/UploadedFile).
        on_stage: Optional callback called at each stage with (stage_number, label).
                  stage_number is 1-indexed.

    Returns:
        (ContractReport, pdf_bytes)
    """
    llm = build_llm()
    embeddings = build_embeddings()

    # Stage 1: Load and chunk
    _notify(on_stage, 1)
    chunks = load_and_chunk(source)

    # Stage 2: Extract clauses
    _notify(on_stage, 2)
    clauses = extract_clauses(chunks, llm)

    # Stage 3 & 4: RAG comparison + risk scoring
    _notify(on_stage, 3)
    vectorstore = get_vectorstore(embeddings)

    _notify(on_stage, 4)
    assessments = score_clauses(clauses, llm, vectorstore)

    # Stage 5: Generate executive summary and report
    _notify(on_stage, 5)
    executive_summary = generate_executive_summary(assessments, llm)

    # Partition assessments by risk level
    flagged = [a for a in assessments if a.risk_level == "flag"]
    review = [a for a in assessments if a.risk_level == "review"]
    ok = [a for a in assessments if a.risk_level == "ok"]
    unclassified = [a for a in assessments if a.risk_level == "unclassified"]

    # Derive document name from source
    if isinstance(source, str):
        doc_name = source.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    else:
        doc_name = getattr(source, "name", "uploaded_contract.pdf")

    report = ContractReport(
        document_name=doc_name,
        total_clauses=len(assessments),
        executive_summary=executive_summary,
        flagged=flagged,
        review=review,
        ok=ok,
        unclassified=unclassified,
    )

    pdf_bytes = generate_report(report)
    return report, pdf_bytes


def get_stage_summary(stage: int, **kwargs) -> str:
    """Generate a human-readable summary for a completed stage."""
    if stage == 1:
        count = kwargs.get("chunk_count", 0)
        return f"Split document into {count} chunks"
    if stage == 2:
        clauses = kwargs.get("clauses", [])
        type_counts = Counter(c.clause_type for c in clauses)
        parts = [f"{v} {k}" for k, v in type_counts.most_common()]
        return f"Found {len(clauses)} clauses: {', '.join(parts)}"
    if stage == 4:
        assessments = kwargs.get("assessments", [])
        level_counts = Counter(a.risk_level for a in assessments)
        return (
            f"Flagged: {level_counts.get('flag', 0)} | "
            f"Review: {level_counts.get('review', 0)} | "
            f"OK: {level_counts.get('ok', 0)} | "
            f"Unclassified: {level_counts.get('unclassified', 0)}"
        )
    return ""


def _notify(callback: Callable[[int, str], None] | None, stage: int) -> None:
    if callback:
        callback(stage, STAGES[stage - 1])
