"""
This module provides service functions for vector store retrieval.

The model decides when to search via a function tool. On a tool call, Collmbo runs the
search through ``litellm.vector_stores.search()`` and returns the results as the tool
output, so no separate LiteLLM proxy is required.
"""

import logging
import os

import litellm
import litellm.vector_stores

from app.env import (
    VECTOR_STORE_IDS,
    VECTOR_STORE_PROVIDER,
    VECTOR_STORE_TOOL_DESCRIPTION,
)
from app.vector_store_logic import (
    build_tool_result_content,
    build_vector_store_tool,
    parse_vector_store_ids,
)


def get_vector_store_tools() -> list[dict]:
    """
    Return the knowledge base search tool when the feature is configured.

    Returns:
        list[dict]: A single-element list with the tool, or an empty list when the
        feature is unconfigured. A missing provider logs a warning and disables it.
    """
    if not VECTOR_STORE_IDS or not parse_vector_store_ids(VECTOR_STORE_IDS):
        return []

    if not VECTOR_STORE_PROVIDER:
        logging.warning(
            "VECTOR_STORE_IDS is set but VECTOR_STORE_PROVIDER is not; "
            "the knowledge base search tool is disabled."
        )
        return []

    return [build_vector_store_tool(VECTOR_STORE_TOOL_DESCRIPTION)]


def run_vector_store_search(query: str) -> str:
    """
    Search the configured vector stores and return the results as tool content.

    A failing search logs a warning and is skipped rather than failing the tool call.

    Args:
        query (str): The search query provided by the model.

    Returns:
        str: The combined search results as the content of a tool message.
    """
    search_responses = []
    for vector_store_id in parse_vector_store_ids(VECTOR_STORE_IDS or ""):
        try:
            search_response = litellm.vector_stores.search(
                vector_store_id=vector_store_id,
                query=query,
                custom_llm_provider=VECTOR_STORE_PROVIDER,
                aws_region_name=os.environ.get("AWS_REGION_NAME"),
            )
        except Exception:
            logging.warning(
                "Vector store search failed for %s; skipping.", vector_store_id
            )
            continue
        search_responses.append(search_response)

    return build_tool_result_content(search_responses)
