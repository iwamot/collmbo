"""
This module contains logic related to LiteLLM.
"""

from litellm.types.utils import ModelResponse


def extract_delta_content(chunk: ModelResponse) -> str | None:
    """
    Extract the delta content from a chunk of model response.

    Args:
        chunk (ModelResponse): The chunk of model response.

    Returns:
        Optional[str]: The delta content, or None if not found.
    """
    if not chunk.choices:
        return None
    delta = chunk.choices[0].get("delta")
    return None if delta is None else delta.get("content")


def is_final_chunk(chunk: ModelResponse) -> bool:
    """
    Check if the chunk is the final chunk of the model response.

    Args:
        chunk (ModelResponse): The chunk of model response.

    Returns:
        bool: True if the chunk is the final chunk, False otherwise.
    """
    return chunk.choices[0].get("finish_reason") is not None


def has_visible_text(content: str) -> bool:
    """
    Check whether streamed assistant content has visible text.

    Reasoning models may end a tool-calling turn with empty or whitespace-only
    content. Such a turn leaves nothing worth preserving in the Slack message, so
    the in-progress placeholder can be reused for the next round rather than
    posting a fresh one.

    Args:
        content (str): The accumulated assistant content for the turn.

    Returns:
        bool: True if the content has non-whitespace text.
    """
    return bool(content and content.strip())
