# Contract Review Pipeline

> AI-powered contract risk analysis that turns legal PDFs into actionable, colour-coded risk reports in under 60 seconds.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Framework-1C3C3C?logo=langchain&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-D97706?logo=anthropic&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)

---

## What It Does

Upload a contract PDF and get back a structured risk report that highlights what to negotiate before signing. The pipeline extracts individual clauses, compares each against a library of standard terms using RAG, and scores every clause as **OK**, **Review**, or **Flag** with a plain-English explanation. Designed for business owners who don't have in-house legal — not lawyers.

## Features

- **PDF-in, PDF-out** — Upload a contract, download a colour-coded risk report
- **Clause extraction** — Automatically identifies and classifies clauses across 8 legal categories
- **RAG comparison** — Each clause is compared against standard terms via vector similarity search
- **Risk scoring** — Every clause gets an ok/review/flag rating with a plain-English reason
- **Executive summary** — AI-generated paragraph highlighting the most critical negotiation points
- **Structure-aware chunking** — Splits on section boundaries, not arbitrary character counts
- **Privacy-first** — Local embeddings (no contract text sent to third parties for embedding), Anthropic no-training header, all LangChain telemetry disabled
- **Dual interface** — CLI for automation, Streamlit UI for interactive use

## How It Works

```
                         Contract PDF
                              │
                              ▼
                 ┌────────────────────────┐
            1.   │   Load & Chunk (PDF)   │  Structure-aware splitting
                 └────────────┬───────────┘  on section boundaries
                              │
                              ▼
                 ┌────────────────────────┐
            2.   │   Extract Clauses      │  Claude identifies & classifies
                 └────────────┬───────────┘  each clause by type
                              │
                              ▼
                 ┌────────────────────────┐
            3.   │   RAG Comparison       │  ChromaDB vector search finds
                 └────────────┬───────────┘  matching standard clause
                              │
                              ▼
                 ┌────────────────────────┐
            4.   │   Risk Scoring         │  Claude compares contract vs
                 └────────────┬───────────┘  standard → ok/review/flag
                              │
                              ▼
                 ┌────────────────────────┐
            5.   │   Report Generation    │  Executive summary +
                 └────────────┬───────────┘  colour-coded PDF via ReportLab
                              │
                              ▼
                      Risk Report PDF
              (red = flag, yellow = review, green = ok)
```

## Quick Start

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### Setup

```bash
# Clone the repo
git clone https://github.com/effiemincer/contract-review-pipeline.git
cd contract-review-pipeline

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Build the standard terms vector store (one-time)
python scripts/build_vectorstore.py
```

### Run

**CLI:**
```bash
python run.py path/to/contract.pdf
```
The risk report PDF is saved alongside the input file and opened automatically.

**Streamlit UI:**
```bash
python -m streamlit run app.py
```
Then open [http://localhost:8501](http://localhost:8501), upload a PDF, and download the report.

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM | Claude claude-sonnet-4-6 (Anthropic) | Clause extraction + risk scoring |
| Framework | LangChain | LLM orchestration and chaining |
| Embeddings | all-MiniLM-L6-v2 (local) | Fully local vector embeddings |
| Vector Store | ChromaDB | Standard terms similarity search |
| PDF Extraction | PyPDFLoader | Contract text extraction |
| Report Output | ReportLab | Colour-coded PDF generation |
| UI | Streamlit | File upload + progress display |
| Data Models | Pydantic | Structured output validation |

## Project Structure

```
contract-review-pipeline/
├── app.py                         # Streamlit UI entry point
├── run.py                         # CLI entry point
├── src/
│   ├── pipeline.py                # 5-stage orchestrator
│   ├── loader.py                  # PDF loading + structure-aware chunking
│   ├── extractor.py               # Clause extraction chain
│   ├── retriever.py               # ChromaDB vector store query
│   ├── scorer.py                  # Risk scoring + executive summary
│   ├── report.py                  # ReportLab PDF generation
│   ├── models.py                  # Pydantic data models
│   └── clients.py                 # LLM/embedding factory + privacy config
├── data/standard_clauses/         # Standard terms library (8 clause types)
├── scripts/build_vectorstore.py   # One-time ChromaDB indexer
├── tests/                         # pytest suite (16 tests)
└── requirements.txt
```

## Testing

```bash
pytest                          # run all 16 tests
pytest tests/test_loader.py     # single file
pytest -k "test_extract"        # pattern match
```

Tests use `FakeListChatModel` to mock LLM calls — no API key needed to run the test suite. Embeddings use the real local model (no mocking needed since it runs on-device).

## Privacy

This tool is designed with contract confidentiality in mind:

- **Embeddings are fully local** — `sentence-transformers` runs on your machine, no contract text is sent externally for embedding
- **Anthropic no-training header** — All API calls include `anthropic-no-training: true`
- **No telemetry** — LangSmith tracing and all LangChain logging are explicitly disabled
- **Ephemeral processing** — No contract content is stored, cached, or persisted after processing

## License

MIT
