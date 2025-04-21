"""
This module contains logic related to LiteLLM.
"""

from typing import Optional

from litellm.utils import get_model_info


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
