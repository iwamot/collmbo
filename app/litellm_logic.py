"""
This module contains logic related to LiteLLM.
"""

from importlib import import_module
from typing import Optional

from litellm.types.utils import ModelResponse


def load_tools_from_module(module_name: Optional[str]) -> Optional[list]:
    """
    Load tools from a module.

    Args:
        module_name (Optional[str]): The name of the module to load tools from.

    Returns:
        Optional[list]: The list of tools from the module, or None if not found.
    """
    return import_module(module_name).tools if module_name is not None else None


def extract_delta_content(chunk: ModelResponse) -> Optional[str]:
    """
    Extract the delta content from a chunk of model response.

    Args:
        chunk (ModelResponse): The chunk of model response.

    Returns:
        Optional[str]: The delta content, or None if not found.
    """
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
