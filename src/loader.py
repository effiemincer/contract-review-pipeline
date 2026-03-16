from __future__ import annotations

import os
import re
import tempfile
from typing import BinaryIO

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

# Regex for major section headings: "1. Title", "2.\n Title", "10. Title", etc.
_SECTION_PATTERN = re.compile(r"\n(?=\d+\.\s)")

# Regex for subsection markers: "(a)", "(b)", "(i)", "(ii)", etc.
_SUBSECTION_PATTERN = re.compile(r"\n(?=\([a-z]+\)\s)")

# Sections larger than this will be sub-split on subsection markers
_MAX_SECTION_CHARS = 3000


def load_and_chunk(source: str | BinaryIO) -> list[Document]:
    """Load a PDF and split into structure-aware chunks that respect clause boundaries.

    Args:
        source: Either a filesystem path (str) or a file-like object (BytesIO/UploadedFile).
    """
    if isinstance(source, str):
        pages = _load_pages(source)
    else:
        pages = _load_pages_from_bytes(source)

    return _split_by_sections(pages)


def _load_pages(path: str) -> list[Document]:
    loader = PyPDFLoader(path)
    return loader.load()


def _load_pages_from_bytes(file_obj: BinaryIO) -> list[Document]:
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        tmp.write(file_obj.read())
        tmp.close()
        return _load_pages(tmp.name)
    finally:
        os.unlink(tmp.name)


def _split_by_sections(pages: list[Document]) -> list[Document]:
    """Combine pages and split on section boundaries, preserving page numbers."""
    if not pages:
        return []

    # Build a single text with page boundary markers so we can map chunks back to pages
    page_offsets: list[tuple[int, int, int]] = []  # (start_offset, end_offset, page_number)
    full_text = ""
    for page in pages:
        start = len(full_text)
        full_text += page.page_content
        end = len(full_text)
        page_number = page.metadata.get("page", 0) + 1
        page_offsets.append((start, end, page_number))
        full_text += "\n"  # separate pages

    # Split on major section boundaries
    raw_sections = _SECTION_PATTERN.split(full_text)
    sections: list[str] = []

    # The first segment is everything before section 1 (preamble/title)
    if raw_sections:
        sections.append(raw_sections[0])
        # Re-attach the leading digit+period that was consumed by the lookahead split
        for part in raw_sections[1:]:
            sections.append(part)

    # Sub-split large sections on subsection markers
    final_chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= _MAX_SECTION_CHARS:
            final_chunks.append(section)
        else:
            # Split on subsection markers like (a), (b)
            sub_parts = _SUBSECTION_PATTERN.split(section)
            if len(sub_parts) <= 1:
                # No subsections found, keep as-is
                final_chunks.append(section)
            else:
                # Keep the section header (text before first subsection) with the first subsection
                header = sub_parts[0].strip()
                for sub in sub_parts[1:]:
                    sub = sub.strip()
                    if sub:
                        # Prepend the section header context to each subsection chunk
                        chunk_text = f"{header}\n{sub}" if header else sub
                        final_chunks.append(chunk_text)

    # Convert to Documents with page number metadata
    documents: list[Document] = []
    for chunk_text in final_chunks:
        # Find which page this chunk starts on
        chunk_start = full_text.find(chunk_text[:80])  # match on first 80 chars
        page_number = _find_page(chunk_start, page_offsets) if chunk_start >= 0 else 1

        documents.append(Document(
            page_content=chunk_text,
            metadata={"page": page_number - 1},  # 0-indexed to match PyPDFLoader convention
        ))

    return documents


def _find_page(offset: int, page_offsets: list[tuple[int, int, int]]) -> int:
    """Find which page a character offset falls on."""
    for start, end, page_number in page_offsets:
        if start <= offset < end:
            return page_number
    # Default to last page
    return page_offsets[-1][2] if page_offsets else 1
