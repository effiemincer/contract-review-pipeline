from __future__ import annotations

import os
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.models import ExtractedClause

VECTORSTORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vectorstore")
STANDARD_CLAUSES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "standard_clauses")
COLLECTION_NAME = "standard_clauses"


def build_vectorstore(embeddings: HuggingFaceEmbeddings) -> None:
    """Read standard clause files and index them into ChromaDB."""
    clauses_dir = Path(STANDARD_CLAUSES_DIR)
    texts: list[str] = []
    metadatas: list[dict] = []

    for txt_file in sorted(clauses_dir.glob("*.txt")):
        clause_type = txt_file.stem.replace("_", " ")
        content = txt_file.read_text(encoding="utf-8").strip()
        texts.append(content)
        metadatas.append({"clause_type": clause_type})

    if not texts:
        raise ValueError(f"No .txt files found in {clauses_dir}")

    Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=embeddings,
        persist_directory=VECTORSTORE_DIR,
        collection_name=COLLECTION_NAME,
    )


def get_vectorstore(embeddings: HuggingFaceEmbeddings) -> Chroma:
    """Load the existing ChromaDB vectorstore."""
    return Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )


def find_standard_match(clause: ExtractedClause, vectorstore: Chroma) -> tuple[str, str]:
    """Find the most similar standard clause for a given extracted clause.

    Returns:
        (standard_clause_text, clause_type_label)
    """
    results = vectorstore.similarity_search(clause.clause_text, k=1)
    if results:
        doc = results[0]
        return doc.page_content, doc.metadata.get("clause_type", "unknown")
    return "", "unknown"
