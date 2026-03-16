"""Streamlit UI for the contract review pipeline."""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from src.clients import configure_privacy

configure_privacy()

import streamlit as st

from src.pipeline import STAGES, run_pipeline

st.set_page_config(page_title="Contract Risk Review", layout="centered")
st.title("Contract Risk Review")
st.caption("Upload a contract PDF to receive a colour-coded risk report.")

# Check for API key
if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error(
        "ANTHROPIC_API_KEY is not set. "
        "Create a `.env` file with your key (see `.env.example`) and restart the app."
    )
    st.stop()

uploaded_file = st.file_uploader("Upload a contract PDF", type=["pdf"])

if uploaded_file is not None:
    if uploaded_file.size == 0:
        st.error("The uploaded file is empty. Please upload a valid PDF.")
        st.stop()

    progress_bar = st.progress(0.0)
    status_containers: dict[int, st.delta_generator.DeltaGenerator] = {}

    def on_stage(stage: int, label: str) -> None:
        # Mark previous stage as complete
        if stage > 1 and (stage - 1) in status_containers:
            status_containers[stage - 1].update(label=STAGES[stage - 2], state="complete")
        # Create new status container
        status_containers[stage] = st.status(label, state="running")
        progress_bar.progress(stage / len(STAGES))

    try:
        report, pdf_bytes = run_pipeline(uploaded_file, on_stage=on_stage)

        # Mark final stage complete
        if len(STAGES) in status_containers:
            status_containers[len(STAGES)].update(
                label=STAGES[-1], state="complete"
            )
        progress_bar.progress(1.0)

        # Results
        st.success(
            f"Report generated! "
            f"**{len(report.flagged)}** flagged, "
            f"**{len(report.review)}** review, "
            f"**{len(report.ok)}** ok, "
            f"**{len(report.unclassified)}** unclassified clauses."
        )

        file_stem = uploaded_file.name.rsplit(".", 1)[0] if "." in uploaded_file.name else uploaded_file.name
        st.download_button(
            label="Download Risk Report",
            data=pdf_bytes,
            file_name=f"{file_stem}_risk_report.pdf",
            mime="application/pdf",
        )

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            st.error("Could not connect to the AI service. Please check your API key.")
        elif "No text" in error_msg or "empty" in error_msg.lower():
            st.error(
                "No clauses could be extracted from this document. "
                "Please ensure it is a text-based PDF (not a scanned image)."
            )
        else:
            st.error(f"An error occurred: {error_msg}")
