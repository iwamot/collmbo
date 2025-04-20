"""
This module contains functions to handle message logic.
"""

import re
from typing import List, Optional, Tuple


def build_system_message(
    system_text_template: str,
    bot_user_id: Optional[str],
    translate_markdown: bool,
) -> dict:
    """
    Build the system message for the bot.

    Args:
        - system_text_template (str): The template for the system message.
        - bot_user_id (Optional[str]): The bot's user ID.
        - translate_markdown (bool): Flag indicating whether to convert Slack mrkdwn to Markdown.

    Returns:
        - dict: The system message as a dictionary with "role" and "content" keys.
    """
    system_text = system_text_template.format(bot_user_id=bot_user_id)
    system_text = maybe_slack_to_markdown(system_text, translate_markdown)
    return {"role": "system", "content": system_text}


def build_assistant_message(text: str) -> dict:
    """
    Build the assistant message for the bot.

    Args:
        - text (str): The text message from the assistant.

    Returns:
        - dict: The assistant message as a dictionary with "role" and "content" keys.
    """
    return {"role": "assistant", "content": text}


def build_user_message(content: list[dict]) -> dict:
    """
    Build the user message.

    Args:
        - content (list[dict]): The content of the user message.

    Returns:
        - dict: The user message as a dictionary with "role" and "content" keys.
    """
    return {"role": "user", "content": content}


def remove_bot_mention(text: str, bot_user_id: Optional[str]) -> str:
    """
    Remove the bot mention from the text.

    Args:
        - text (str): The input text containing the bot mention.
        - bot_user_id (Optional[str]): The bot's user ID.

    Returns:
        - str: The text with the bot mention removed.
    """
    return re.sub(rf"<@{bot_user_id}>\s*", "", text) if bot_user_id else text


def maybe_redact_string(
    input_string: str,
    patterns: List[Tuple[str, str]],
    redaction_enabled: bool,
) -> str:
    """
    Optionally redact sensitive information from a string (inspired by @quangnhut123)

    Args:
        - input_string (str): The string to potentially redact
        - patterns (list[tuple]): A list of (regex pattern, replacement string)
        - redaction_enabled (bool): Whether redaction should be applied

    Returns:
        - str: The redacted string (or original if disabled)
    """
    if not redaction_enabled:
        return input_string
    output_string = input_string
    for pattern, replacement in patterns:
        output_string = re.sub(pattern, replacement, output_string)
    return output_string


def unescape_slack_formatting(content: str) -> str:
    """
    Unescape Slack formatting characters.

    Unescape &, < and >, since Slack replaces these with their HTML equivalents.
    See also: https://api.slack.com/reference/surfaces/formatting#escaping

    Args:
        content (str): The input string containing Slack formatting.

    Returns:
        str: The unescaped string.
    """
    return content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def maybe_slack_to_markdown(content: str, translate_markdown: bool) -> str:
    """
    Convert Slack mrkdwn to Markdown format.

    See also: https://api.slack.com/reference/surfaces/formatting#basics

    Args:
        content (str): The input string in Slack mrkdwn format.
        translate_markdown (bool): Flag indicating whether to perform the conversion.

    Returns:
        str: The converted string in Markdown format.
    """
    if not translate_markdown:
        return content

    # Split the input string into parts based on code blocks and inline code
    parts = re.split(r"(?s)(```.+?```|`[^`\n]+?`)", content)

    # Apply the bold, italic, and strikethrough formatting to text not within code
    result = ""
    for part in parts:
        if not part.startswith("```") and not part.startswith("`"):
            for o, n in [
                (r"\*(?!\s)([^\*\n]+?)(?<!\s)\*", r"**\1**"),  # *bold* to **bold**
                (r"_(?!\s)([^_\n]+?)(?<!\s)_", r"*\1*"),  # _italic_ to *italic*
                (r"~(?!\s)([^~\n]+?)(?<!\s)~", r"~~\1~~"),  # ~strike~ to ~~strike~~
            ]:
                part = re.sub(o, n, part)
        result += part
    return result


def build_slack_user_prefixed_text(reply: dict, text: str) -> str:
    """
    Build a Slack user-prefixed text message.

    Args:
        reply (dict): The reply dictionary containing user information.
        text (str): The text message to be prefixed.

    Returns:
        str: The formatted text message with user mention.
    """
    user_identifier = reply.get("user", reply.get("username"))
    return f"<@{user_identifier}>: {text}"


def maybe_set_cache_points(
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
    for message in reversed(messages):  # pragma: no branch
        if message.get("role") != "user":
            continue
        message["content"][-1]["cache_control"] = {"type": "ephemeral"}
        user_messages_found += 1
        if user_messages_found >= 2:
            break
