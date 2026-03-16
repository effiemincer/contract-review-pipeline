from __future__ import annotations

from io import BytesIO

from src.loader import load_and_chunk


def test_load_from_path(sample_pdf_path):
    chunks = load_and_chunk(sample_pdf_path)
    assert len(chunks) > 0
    assert all(hasattr(c, "page_content") for c in chunks)
    assert all("page" in c.metadata for c in chunks)


def test_load_from_bytes(sample_pdf_path):
    with open(sample_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    file_obj = BytesIO(pdf_bytes)
    chunks = load_and_chunk(file_obj)
    assert len(chunks) > 0
    assert all(hasattr(c, "page_content") for c in chunks)
