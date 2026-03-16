from __future__ import annotations

import os

from langchain_core.globals import set_debug, set_verbose
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings


def configure_privacy() -> None:
    """Disable all LangChain telemetry and logging. Call before using any chains."""
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ.setdefault("LANGCHAIN_API_KEY", "")
    set_verbose(False)
    set_debug(False)


def build_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0,
        default_headers={"anthropic-no-training": "true"},
    )


def build_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
