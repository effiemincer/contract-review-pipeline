"""One-time script to index standard clauses into ChromaDB."""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.clients import build_embeddings, configure_privacy
from src.retriever import build_vectorstore

configure_privacy()


def main() -> None:
    print("Building standard terms vector store...")
    embeddings = build_embeddings()
    build_vectorstore(embeddings)
    print("Vector store built successfully at vectorstore/")


if __name__ == "__main__":
    main()
