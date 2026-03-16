from __future__ import annotations

import json
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.models import ExtractedClause

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a legal document analyst. You identify discrete legal clauses in contract text.",
    ),
    (
        "human",
        """Read the following contract text and identify all discrete legal clauses.

For each clause, output a JSON array of objects with these fields:
- clause_type: the category. Use one of: indemnification, limitation of liability, termination, ip ownership, governing law, payment terms, confidentiality, dispute resolution. If the clause does not match any of these, use "unclassified".
- clause_text: the exact text of the clause
- page_number: {page_number}

If no clauses are present in this chunk, return an empty JSON array [].

Return ONLY the JSON array, no other text.

Contract text:
{text}""",
    ),
])


def extract_clauses(chunks: list[Document], llm: ChatAnthropic) -> list[ExtractedClause]:
    """Extract and classify clauses from document chunks."""
    chain = EXTRACTION_PROMPT | llm | StrOutputParser()
    clauses: list[ExtractedClause] = []

    for chunk in chunks:
        page_number = chunk.metadata.get("page", 0) + 1
        raw = chain.invoke({"text": chunk.page_content, "page_number": page_number})
        result = _parse_json_lenient(raw)

        if isinstance(result, list):
            for item in result:
                clauses.append(ExtractedClause(**item))

    return clauses


def _parse_json_lenient(text: str) -> list | dict:
    """Parse JSON from LLM output, handling markdown fences and trailing commas."""
    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return json.loads(text)
