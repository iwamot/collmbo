"""
This module contains logical functions for vector store retrieval.
"""

from litellm.types.vector_stores import VectorStoreSearchResponse

VECTOR_STORE_TOOL_NAME = "collmbo_search_knowledge_base"
NO_RESULTS_MESSAGE = "No relevant information was found in the knowledge base."


def parse_vector_store_ids(raw: str) -> list[str]:
    """
    Parse a comma-separated list of vector store IDs.

    Args:
        raw (str): The raw comma-separated value.

    Returns:
        list[str]: The parsed IDs with surrounding whitespace stripped and empties dropped.
    """
    return [item.strip() for item in raw.split(",") if item.strip()]


def build_vector_store_tool(description: str) -> dict:
    """
    Build the function tool definition the model calls to search the knowledge base.

    Args:
        description (str): The tool description shown to the model. It guides when the
            model searches, so it can be tailored to the contents of the knowledge base.

    Returns:
        dict: The tool definition in OpenAI function-calling format.
    """
    return {
        "type": "function",
        "function": {
            "name": VECTOR_STORE_TOOL_NAME,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    },
                },
                "required": ["query"],
            },
        },
    }


def build_tool_result_content(
    search_responses: list[VectorStoreSearchResponse],
) -> str:
    """
    Combine vector store search responses into the content of a tool message.

    Args:
        search_responses (list[VectorStoreSearchResponse]): The responses, one per store.

    Returns:
        str: The concatenated result texts, or a fallback message when there are none.
    """
    texts: list[str] = []
    for search_response in search_responses:
        data = search_response.get("data")
        if not data:
            continue
        for result in data:
            result_content = result.get("content")
            if not result_content:
                continue
            for content_item in result_content:
                text = content_item.get("text")
                if text:
                    texts.append(text)

    if not texts:
        return NO_RESULTS_MESSAGE
    return "\n\n".join(texts)
