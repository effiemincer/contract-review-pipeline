# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Contract Review Pipeline — a LangChain-powered tool that accepts a contract PDF and produces a colour-coded risk report. It extracts clauses, compares each against a standard terms library via RAG, and flags deviations with plain-English explanations. Target user is a non-technical business owner.

The PRD (`PRD.md`) is the authoritative spec. Refer to it for prompt templates, data model definitions, and detailed stage descriptions.

## Tech Stack

- **Language:** Python 3.11+
- **LLM framework:** LangChain with Claude (claude-sonnet-4-6 via Anthropic API)
- **Embeddings:** HuggingFace `all-MiniLM-L6-v2` (fully local via sentence-transformers)
- **Vector store:** ChromaDB (local)
- **PDF extraction:** LangChain PyPDFLoader
- **Output parsing:** LangChain JSON output parser
- **UI:** Streamlit (file upload + progress display)
- **Report output:** ReportLab (PDF generation)
- **Testing:** pytest

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Build the standard terms vector store (one-time setup)
python scripts/build_vectorstore.py

# Run via CLI
python run.py <path_to_contract.pdf>

# Run Streamlit demo UI
streamlit run app.py

# Run tests
pytest
pytest tests/test_loader.py         # single file
pytest -k "test_extract"            # pattern match
```

## Architecture

Five-stage pipeline orchestrated by `src/pipeline.py`, which both entry points (`run.py`, `app.py`) call via `run_pipeline()`. Each stage lives in its own module under `src/`:

1. **Loading & Chunking** (`src/loader.py`) — Accepts `str` path (CLI) or `BinaryIO` (Streamlit). PyPDFLoader extracts text; RecursiveCharacterTextSplitter creates 500-token chunks with 100-token overlap. Streamlit path uses a tempfile bridge with `delete=False` for Windows compatibility.
2. **Clause Extraction** (`src/extractor.py`) — LLM chain identifies discrete clauses, classifies by type (8 known types + `unclassified`), outputs `ExtractedClause` models.
3. **RAG Comparison** (`src/retriever.py`) — Each clause embedded and matched against ChromaDB standard terms store; top-1 match retrieved.
4. **Risk Scoring** (`src/scorer.py`) — LLM comparison chain scores each clause as `ok`, `review`, or `flag` with plain-English reason; outputs `ClauseRiskAssessment` models. Unclassified clauses skip LLM scoring.
5. **Report Generation** (`src/report.py`) — Assembles `ContractReport` and renders a colour-coded PDF via ReportLab (red=flag, yellow=review, green=ok). Returns `bytes`.

**Supporting modules:**
- `src/models.py` — Pydantic data models: `ExtractedClause`, `ClauseRiskAssessment`, `ContractReport`
- `src/clients.py` — Factory functions for LLM and embeddings; `configure_privacy()` disables all LangChain telemetry/tracing

**Standard clauses** source text lives in `data/standard_clauses/` (8 `.txt` files). ChromaDB store built by `scripts/build_vectorstore.py`, persisted in `vectorstore/` (gitignored).

## Key Clause Types

indemnification, limitation of liability, termination, IP ownership, governing law, payment terms, confidentiality, dispute resolution. Anything else → `unclassified` (no risk score, no standard comparison).

## Privacy Constraints

- Contract content must **never** be stored, logged, or persisted outside the local process
- Embeddings are fully local (sentence-transformers) — no contract text sent to third parties for embedding
- Anthropic API calls use `anthropic-no-training: true` header (set via `default_headers` in `src/clients.py`)
- LangChain tracing/LangSmith disabled via `configure_privacy()` — called at startup in both entry points
- The `vectorstore/` directory contains only standard terms, never user contracts
