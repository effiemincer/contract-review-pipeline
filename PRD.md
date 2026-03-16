# PRD: Contract Review Pipeline

**Project type:** LangChain demo  
**Status:** Draft  
**Author:** AI Systems Team  
**Last updated:** March 2026

---

## 1. Overview

### Problem statement

Small and medium businesses sign contracts regularly — vendor agreements, service contracts, NDAs, employment agreements — but rarely have in-house legal expertise to review them. Hiring a lawyer for routine contract review costs $300–$600/hour and takes days. As a result, businesses either sign contracts blind or delay deals while waiting for legal review.

### Proposed solution

A LangChain-powered pipeline that accepts a contract PDF as input and produces a structured risk report as output. The pipeline extracts individual clauses, compares each clause against a library of pre-approved standard terms using RAG, and flags deviations with a plain-English explanation of the risk. The output is a colour-coded report a non-lawyer business owner can act on in minutes.

### Success criteria

- Pipeline processes a 10-page contract end-to-end in under 60 seconds
- Correctly identifies and labels at least 80% of key clause types in test contracts
- Risk flags are understandable to a non-legal user without further explanation
- Demo can be run live against a realistic dummy contract with compelling, accurate output

---

## 2. Target user

**Primary:** Business owner or operations manager at an SME (5–200 employees) who regularly receives vendor or client contracts and has no legal staff. They are not technical — they will not use a CLI. The interface must be a simple, self-contained UI they can run locally without developer help.

**User's job to be done:** "I need to know whether this contract is safe to sign, and what I should push back on, without paying a lawyer."

---

## 3. Scope

### In scope

- PDF contract ingestion and text extraction
- Automatic clause segmentation, type classification, and unclassified clause capture
- RAG-based comparison against a standard terms library sourced from publicly available model contract templates
- Per-clause risk scoring (OK / review / flag) with plain-English reasoning
- Final structured output rendered as a generated PDF report the user can save or share
- A pre-built standard terms library covering the 8 most common clause types (see section 6)

### Out of scope (v1)

- User authentication or multi-user support
- Storing or persisting contracts after processing
- Editable output or redline generation
- Integration with DocuSign, Google Drive, or other document platforms
- Support for Word (.docx) or other non-PDF formats
- Jurisdiction-specific legal advice or compliance checking
- Custom or company-specific standard terms (generic public templates only in v1)
- Any server-side storage, logging, or persistence of contract content — all processing is ephemeral and local

---

## 4. User flow

1. User runs the pipeline from the command line (or a minimal Streamlit UI for demo purposes), providing the path to a contract PDF.
2. The pipeline loads the PDF, chunks the text, and runs clause extraction — outputting a list of identified clauses with their type labels.
3. Each clause is embedded and compared against the standard terms vector store. The closest matching standard clause is retrieved for each.
4. A second LLM call compares the contract clause to the standard clause and outputs a risk label and explanation.
5. The pipeline assembles a final report and renders it as a formatted PDF — clauses grouped by risk level, colour-coded, with the matched standard clause shown alongside each flag.
6. The user opens the PDF, reviews flagged clauses, and decides which to negotiate before signing.

---

## 5. Technical architecture

### Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| LLM framework | LangChain |
| LLM | Claude (claude-sonnet-4-6 via Anthropic API) |
| Embeddings | OpenAI text-embedding-3-small or Claude embeddings |
| Vector store | ChromaDB (local, for demo) |
| PDF loader | LangChain PyPDFLoader |
| Output parsing | LangChain Pydantic output parser |
| Demo UI | Streamlit — file upload + progress display |
| Report output | Generated PDF via ReportLab or WeasyPrint |

### Privacy constraints

External APIs (Anthropic, OpenAI embeddings) are permitted, but contract content must never be stored, logged, or cached outside of the local process. All API calls must be stateless — no conversation history, no fine-tuning data, no server-side logging enabled. The Anthropic API is used with `anthropic-no-training: true` header where supported.

### Pipeline stages

**Stage 1 — Document loading and chunking**

- `PyPDFLoader` extracts raw text from the uploaded PDF
- `RecursiveCharacterTextSplitter` splits into overlapping chunks (500 tokens, 100-token overlap) to preserve clause boundaries
- Chunks are stored with page number metadata for source attribution in the final report

**Stage 2 — Clause extraction**

- An LLM extraction chain processes each chunk and identifies discrete clauses
- For each clause, the chain outputs: clause type, clause text verbatim, and page number
- Clause types to detect: indemnification, limitation of liability, termination, IP ownership, governing law, payment terms, confidentiality, dispute resolution
- Clauses that do not match a known type are labelled `unclassified` and included in the report without a risk score or standard comparison
- Output is parsed into a typed Pydantic model (`ExtractedClause`)

**Stage 3 — RAG comparison**

- Each extracted clause is embedded and used to query the standard terms vector store
- The top-1 most similar standard clause is retrieved
- The contract clause and standard clause are passed together to an LLM comparison chain

**Stage 4 — Risk scoring**

- The comparison chain outputs a structured risk assessment per clause:
  - `risk_level`: one of `ok`, `review`, or `flag`
  - `reason`: a 1–2 sentence plain-English explanation of the risk or lack thereof
  - `standard_clause_reference`: the label of the matched standard clause
- Output is parsed into a typed Pydantic model (`ClauseRiskAssessment`)

**Stage 5 — Report generation**

- All clause assessments are assembled into a final `ContractReport` object
- Report is rendered as a formatted PDF with three sections: flagged clauses, clauses for review, and passed clauses
- Each flagged or review clause shows: the clause text, the matched standard clause, the risk label, and the plain-English reason
- The PDF is saved to the same directory as the input file and opened automatically

### Data models

```python
class ExtractedClause(BaseModel):
    clause_type: str  # known type or "unclassified"
    clause_text: str
    page_number: int

class ClauseRiskAssessment(BaseModel):
    clause_type: str
    clause_text: str
    risk_level: Literal["ok", "review", "flag", "unclassified"]
    reason: str | None  # None for unclassified clauses
    standard_clause_reference: str | None  # None for unclassified clauses

class ContractReport(BaseModel):
    document_name: str
    total_clauses: int
    flagged: list[ClauseRiskAssessment]
    review: list[ClauseRiskAssessment]
    ok: list[ClauseRiskAssessment]
    unclassified: list[ClauseRiskAssessment]
```

---

## 6. Standard terms library

The vector store is pre-populated at setup time with approved example clauses for each of the following types. These serve as the RAG knowledge base against which incoming contract clauses are compared.

| Clause type | Risk focus |
|---|---|
| Indemnification | Unilateral vs mutual protection |
| Limitation of liability | Cap amount, excluded damages |
| Termination | Notice period, for-cause vs at-will |
| IP ownership | Work-for-hire, assignment of rights |
| Governing law | Jurisdiction favourability |
| Payment terms | Net days, late fees, dispute process |
| Confidentiality | Duration, permitted disclosures |
| Dispute resolution | Arbitration vs litigation, venue |

Standard clauses will be sourced from publicly available model contract templates and lightly edited for demo purposes. Each standard clause is stored in ChromaDB with its type label as metadata.

---

## 7. Prompts

### Clause extraction prompt (simplified)

```
You are a legal document analyst. Read the following contract text and identify all discrete legal clauses.

For each clause, output:
- clause_type: the category (e.g. indemnification, termination, governing law)
- clause_text: the exact text of the clause
- page_number: the page it appears on

If no clauses are present in this chunk, return an empty list.

Contract text:
{text}
```

### Risk scoring prompt (simplified)

```
You are a contract risk analyst. Compare the following contract clause against the standard acceptable version.

Contract clause ({clause_type}):
{contract_clause}

Standard acceptable clause:
{standard_clause}

Assess the risk to the party receiving this contract. Output:
- risk_level: "ok" if acceptable, "review" if it warrants discussion, "flag" if it poses significant risk
- reason: 1–2 sentences explaining the key difference and why it matters

Be direct and use plain English. Avoid legal jargon.
```

---

## 8. Project structure

```
contract-review/
├── data/
│   └── standard_clauses/       # Source text for standard terms library
├── vectorstore/                # ChromaDB persistent store (gitignored)
├── src/
│   ├── loader.py               # PDF loading and chunking
│   ├── extractor.py            # Clause extraction chain
│   ├── retriever.py            # Vector store setup and query
│   ├── scorer.py               # Risk scoring chain
│   ├── report.py               # Report assembly and PDF generation
│   └── models.py               # Pydantic data models
├── scripts/
│   └── build_vectorstore.py    # One-time script to index standard clauses
├── app.py                      # Streamlit UI entry point (file upload → PDF output)
├── requirements.txt
├── CLAUDE.md                   # Claude Code configuration
└── PRD.md                      # This document
```

---

## 9. Build sequence

1. Set up project skeleton and install dependencies
2. Build and validate data models (`models.py`)
3. Implement PDF loader and chunker (`loader.py`)
4. Source and format standard clauses; build vector store (`build_vectorstore.py`)
5. Implement clause extraction chain with prompt and output parser (`extractor.py`)
6. Implement RAG retrieval (`retriever.py`)
7. Implement risk scoring chain (`scorer.py`)
8. Assemble report generation (`report.py`)
9. Wire together in CLI runner (`run.py`)
10. Build Streamlit UI for demo (`app.py`)
11. Test end-to-end with dummy contract
12. Iterate on prompts based on output quality

---

## 10. Decisions log

| Question | Decision |
|---|---|
| Who is the end user? | Business owner running a local Streamlit UI — not a developer, not a CLI user |
| Where do standard terms come from? | Generic public model contract templates, curated at build time |
| What is the output format? | Generated PDF report saved locally |
| What happens with unrecognised clauses? | Captured as `unclassified` in the report with no risk score |
| Data privacy approach? | External APIs permitted; no contract content may be stored, logged, or persisted outside the local process |