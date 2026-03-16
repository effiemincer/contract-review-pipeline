"""CLI entry point for the contract review pipeline."""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.clients import configure_privacy

configure_privacy()

from src.pipeline import STAGES, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse a contract PDF and generate a risk report.")
    parser.add_argument("pdf_path", help="Path to the contract PDF file")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the generated report")
    args = parser.parse_args()

    pdf_path = args.pdf_path
    if not os.path.isfile(pdf_path):
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if not pdf_path.lower().endswith(".pdf"):
        print("Error: File must be a PDF", file=sys.stderr)
        sys.exit(1)

    def on_stage(stage: int, label: str) -> None:
        print(f"[{stage}/{len(STAGES)}] {label}...")

    report, pdf_bytes = run_pipeline(pdf_path, on_stage=on_stage)

    # Write output PDF
    input_path = Path(pdf_path)
    output_path = input_path.parent / f"{input_path.stem}_risk_report.pdf"
    output_path.write_bytes(pdf_bytes)
    print(f"\nReport saved to: {output_path}")
    print(
        f"Summary: {len(report.flagged)} flagged, {len(report.review)} review, "
        f"{len(report.ok)} ok, {len(report.unclassified)} unclassified"
    )

    if not args.no_open:
        _open_file(str(output_path))


def _open_file(path: str) -> None:
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


if __name__ == "__main__":
    main()
