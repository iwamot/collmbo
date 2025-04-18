"""
This module contains functions to handle message logic.
"""


def set_cache_points_if_needed(
    messages: list[dict],
    total_tokens: int,
    prompt_cache_enabled: bool,
) -> None:
    """
    Set cache points in user messages if certain conditions are met.

    Args:
        messages (list[dict]): The list of messages.
        total_tokens (int): The total number of tokens.
        prompt_cache_enabled (bool): Flag indicating if prompt caching is enabled.

    Returns:
        None
    """
    if not (
        prompt_cache_enabled
        and total_tokens >= 1024
        and len([m for m in messages if m.get("role") == "user"]) >= 2
    ):
        return
    user_messages_found = 0
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        message["content"][-1]["cache_control"] = {"type": "ephemeral"}
        user_messages_found += 1
        if user_messages_found >= 2:
            break
