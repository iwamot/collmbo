"""
This module contains logic related to LiteLLM.
"""

from importlib import import_module
from typing import Optional

from litellm.utils import get_model_info, token_counter


def get_max_input_tokens(model_type: str) -> Optional[int]:
    """
    Get the maximum input tokens for a given model type.

    Args:
        model_type (str): The type of the model.

    Returns:
        Optional[int]: The maximum input tokens for the model type, or None if not found.
    """
    model_info = get_model_info(model_type)
    return model_info.get("max_input_tokens") or model_info.get("max_tokens")


def calculate_max_context_tokens(
    max_input_tokens: int,
    tools_tokens: int,
    max_output_tokens: int,
) -> int:
    """
    Calculate the maximum context tokens based on input, output, and tools tokens.

    Args:
        max_input_tokens (int): The maximum input tokens.
        tools_tokens (int): The number of tokens used by tools.
        max_output_tokens (int): The maximum output tokens.

    Returns:
        int: The maximum context tokens.
    """
    return max(0, max_input_tokens - tools_tokens - max_output_tokens)


def trim_messages_to_max_context_tokens(
    messages: list[dict],
    model_type: str,
    max_context_tokens: int,
) -> int:
    """
    Trim messages to fit within the maximum context tokens.

    Args:
        messages (list[dict]): The list of messages to trim.
        model_type (str): The type of the model.
        max_context_tokens (int): The maximum context tokens.

    Returns:
        int: The number of tokens in the trimmed messages.
    """
    while True:
        messages_tokens = token_counter(model=model_type, messages=messages)
        if messages_tokens <= max_context_tokens:
            break
        # Leaving only the system message makes the prompt meaningless
        if len(messages) == 2:
            return messages_tokens
        for i, message in enumerate(messages):
            if message["role"] in ("user", "assistant", "function"):
                del messages[i]
                break
        else:
            # Fall through and let the LiteLLM error handler deal with it
            break
    return messages_tokens


def load_tools_from_module(module_name: Optional[str]) -> Optional[list]:
    """
    Load tools from a module.

    Args:
        module_name (Optional[str]): The name of the module to load tools from.

    Returns:
        Optional[list]: The list of tools from the module, or None if not found.
    """
    return import_module(module_name).tools if module_name is not None else None
