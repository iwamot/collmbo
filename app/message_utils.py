import logging
import re
from typing import List, Optional, Sequence, Tuple

from slack_bolt import BoltContext

from app.env import (
    IMAGE_FILE_ACCESS_ENABLED,
    PDF_FILE_ACCESS_ENABLED,
    REDACT_CREDIT_CARD_PATTERN,
    REDACT_EMAIL_PATTERN,
    REDACT_PHONE_PATTERN,
    REDACT_SSN_PATTERN,
    REDACT_USER_DEFINED_PATTERN,
    REDACTION_ENABLED,
    SYSTEM_TEXT,
    TRANSLATE_MARKDOWN,
)
from app.litellm_image_ops import get_image_content_if_exists
from app.litellm_pdf_ops import get_pdf_content_if_exists

REDACT_PATTERNS = [
    (REDACT_EMAIL_PATTERN, "[EMAIL]"),
    (REDACT_CREDIT_CARD_PATTERN, "[CREDIT CARD]"),
    (REDACT_PHONE_PATTERN, "[PHONE]"),
    (REDACT_SSN_PATTERN, "[SSN]"),
    (REDACT_USER_DEFINED_PATTERN, "[REDACTED]"),
]


# Conversion from Slack mrkdwn to Markdown
# See also: https://api.slack.com/reference/surfaces/formatting#basics
def maybe_slack_to_markdown(content: str) -> str:
    if not TRANSLATE_MARKDOWN:
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


def maybe_redact_string(
    input_string: str,
    patterns: List[Tuple[str, str]],
    redaction_enabled: bool = True,
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


def build_system_message(bot_user_id: Optional[str]) -> dict:
    system_text = SYSTEM_TEXT.format(bot_user_id=bot_user_id)
    system_text = maybe_slack_to_markdown(system_text)
    return {"role": "system", "content": system_text}


# Format message from Slack to send to LiteLLM
def format_litellm_message_content(content: str) -> str:
    # Unescape &, < and >, since Slack replaces these with their HTML equivalents
    # See also: https://api.slack.com/reference/surfaces/formatting#escaping
    return content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def can_bot_read_files(bot_scopes: Optional[Sequence[str]]) -> bool:
    return bot_scopes is not None and "files:read" in bot_scopes


def convert_replies_to_messages(
    replies: list[dict],
    context: BoltContext,
    logger: logging.Logger,
) -> list[dict]:
    messages: list[dict] = []
    pdf_count = 0

    # Process replies in reverse order to prioritize recent PDFs and avoid unnecessary downloads
    reversed_replies = list(reversed(replies))

    for reply in reversed_replies:
        reply_text = re.sub(
            f"<@{context.bot_user_id}>\\s*", "", reply.get("text") or ""
        )
        reply_text = maybe_redact_string(reply_text, REDACT_PATTERNS, REDACTION_ENABLED)
        reply_text = format_litellm_message_content(reply_text)
        reply_text = maybe_slack_to_markdown(reply_text)
        content = [
            {
                "type": "text",
                "text": f"<@{reply.get('user', reply.get('username'))}>: {reply_text}",
            }
        ]

        if reply["user"] == context.bot_user_id:
            messages.append({"role": "assistant", "content": content[0]["text"]})
            continue

        if (
            reply.get("bot_id") is None
            and context.authorize_result is not None
            and IMAGE_FILE_ACCESS_ENABLED
            and can_bot_read_files(context.authorize_result.bot_scopes)
        ):
            if context.bot_token is None:
                raise ValueError("context.bot_token cannot be None")
            content += get_image_content_if_exists(
                bot_token=context.bot_token,
                files=reply.get("files"),
                logger=logger,
            )

        # Only process PDFs if we haven't reached the limit of 5
        if (
            pdf_count < 5
            and reply.get("bot_id") is None
            and context.authorize_result is not None
            and PDF_FILE_ACCESS_ENABLED
            and can_bot_read_files(context.authorize_result.bot_scopes)
        ):
            if context.bot_token is None:
                raise ValueError("context.bot_token cannot be None")

            pdf_content = get_pdf_content_if_exists(
                bot_token=context.bot_token,
                files=reply.get("files"),
                logger=logger,
                max_pdfs=5,
                current_pdf_count=pdf_count,
            )

            # Count and add PDFs
            pdf_count += len(pdf_content)
            content += pdf_content

        messages.append({"role": "user", "content": content})

    # Reverse the messages to restore chronological order
    messages.reverse()
    return messages
