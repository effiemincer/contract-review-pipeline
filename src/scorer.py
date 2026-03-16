from __future__ import annotations

import json
import re

from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.models import ClauseRiskAssessment, ExtractedClause
from src.retriever import find_standard_match

SCORING_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a contract risk analyst. You compare contract clauses against standard acceptable versions and assess risk.",
    ),
    (
        "human",
        """Compare the following contract clause against the standard acceptable version.

Contract clause ({clause_type}):
{contract_clause}

Standard acceptable clause:
{standard_clause}

Assess the risk to the party receiving this contract. Output a JSON object with:
- risk_level: "ok" if acceptable, "review" if it warrants discussion, "flag" if it poses significant risk
- reason: 1-2 sentences explaining the key difference and why it matters

Be direct and use plain English. Avoid legal jargon.

Return ONLY the JSON object, no other text.""",
    ),
])

UNCLASSIFIED_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a contract risk analyst. You assess contract clauses for potential risks to the receiving party.",
    ),
    (
        "human",
        """Analyse the following contract clause that does not fall into a standard category.

Contract clause:
{contract_clause}

Assess the risk to the party receiving this contract. Output a JSON object with:
- risk_level: "ok" if acceptable, "review" if it warrants discussion, "flag" if it poses significant risk
- reason: 1-2 sentences explaining any concerns or why it is acceptable

Be direct and use plain English. Avoid legal jargon.

Return ONLY the JSON object, no other text.""",
    ),
])


def score_clauses(
    clauses: list[ExtractedClause],
    llm: ChatAnthropic,
    vectorstore: Chroma,
) -> list[ClauseRiskAssessment]:
    """Score each clause by comparing against the standard terms library."""
    classified_chain = SCORING_PROMPT | llm | StrOutputParser()
    unclassified_chain = UNCLASSIFIED_PROMPT | llm | StrOutputParser()
    assessments: list[ClauseRiskAssessment] = []

    for clause in clauses:
        if clause.clause_type == "unclassified":
            raw = unclassified_chain.invoke({
                "contract_clause": clause.clause_text,
            })
            result = _parse_json_lenient(raw)
            assessments.append(ClauseRiskAssessment(
                clause_type=clause.clause_type,
                clause_text=clause.clause_text,
                risk_level=result.get("risk_level", "review"),
                reason=result.get("reason", ""),
                standard_clause_reference=None,
            ))
            continue

        standard_text, standard_label = find_standard_match(clause, vectorstore)

        raw = classified_chain.invoke({
            "clause_type": clause.clause_type,
            "contract_clause": clause.clause_text,
            "standard_clause": standard_text,
        })
        result = _parse_json_lenient(raw)

        assessments.append(ClauseRiskAssessment(
            clause_type=clause.clause_type,
            clause_text=clause.clause_text,
            risk_level=result.get("risk_level", "review"),
            reason=result.get("reason", ""),
            standard_clause_reference=standard_label,
        ))

    return assessments


SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a contract risk analyst writing an executive summary for a non-lawyer business owner.",
    ),
    (
        "human",
        """Below are the risk assessments for a contract. Write a short paragraph (3-5 sentences) summarising the most critical points the reader should discuss or negotiate before signing. Focus on the flagged and review items. Be direct, specific, and use plain English.

{assessments}

Return ONLY the summary paragraph, no other text.""",
    ),
])


def generate_executive_summary(
    assessments: list[ClauseRiskAssessment],
    llm: ChatAnthropic,
) -> str:
    """Generate a plain-English executive summary of the most critical risks."""
    chain = SUMMARY_PROMPT | llm | StrOutputParser()

    # Build a concise text representation of flagged and review items
    critical = [a for a in assessments if a.risk_level in ("flag", "review")]
    if not critical:
        return "No significant risks were identified in this contract."

    lines = []
    for a in critical:
        lines.append(f"- [{a.risk_level.upper()}] {a.clause_type.title()}: {a.reason}")

    return chain.invoke({"assessments": "\n".join(lines)})


def _parse_json_lenient(text: str) -> dict:
    """Parse JSON from LLM output, handling markdown fences and trailing commas."""
    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return json.loads(text)
