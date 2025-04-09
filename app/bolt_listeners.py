import logging
import re
import time
from typing import List, Optional, Sequence, Tuple

from litellm.exceptions import Timeout
from slack_bolt import BoltContext
from slack_sdk.web import SlackResponse, WebClient

from app.bolt_utils import extract_user_id_from_context
from app.env import (
    ANTHROPIC_PROMPT_CACHING_ENABLED,
    IMAGE_FILE_ACCESS_ENABLED,
    LITELLM_TIMEOUT_SECONDS,
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
from app.exceptions import ContextOverflowError
from app.i18n import translate
from app.litellm_image_ops import get_image_content_if_exists
from app.litellm_ops import messages_within_context_window, reply_to_slack_with_litellm
from app.litellm_pdf_ops import get_pdf_content_if_exists
from app.slack_utils import is_in_thread_started_by_app_mention, is_this_app_mentioned

TIMEOUT_ERROR_MESSAGE = (
    f":warning: Apologies! It seems that the AI didn't respond within the {LITELLM_TIMEOUT_SECONDS}-second timeframe. "
    "Please try your request again later. "
    "If you wish to extend the timeout limit, "
    "you may consider deploying this app with customized settings on your infrastructure. :bow:"
)
LOADING_TEXT = ":hourglass_flowing_sand: Wait a second, please ..."


def initialize_messages(
    system_text_template: str, bot_user_id: Optional[str], translate_markdown: bool
) -> list[dict]:
    system_text = system_text_template.format(bot_user_id=bot_user_id)
    system_text = maybe_slack_to_markdown(system_text, translate_markdown)
    return [{"role": "system", "content": system_text}]


def get_thread_replies(client: WebClient, channel: str, thread_ts: str) -> list[dict]:
    return client.conversations_replies(
        channel=channel,
        ts=thread_ts,
        limit=1000,
    ).get("messages", [])


def get_dm_replies(client: WebClient, channel: str) -> list[dict]:
    past_messages: list[dict] = client.conversations_history(
        channel=channel,
        limit=100,
        oldest=f"{time.time() - 86400:.6f}",  # 24 hours ago
        inclusive=True,
    ).get("messages", [])
    return list(reversed(past_messages))


def can_bot_read_files(bot_scopes: Optional[Sequence[str]]) -> bool:
    return bot_scopes is not None and "files:read" in bot_scopes


# Format message from Slack to send to LiteLLM
def format_litellm_message_content(content: str) -> str:
    # Unescape &, < and >, since Slack replaces these with their HTML equivalents
    # See also: https://api.slack.com/reference/surfaces/formatting#escaping
    return content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


# Conversion from Slack mrkdwn to Markdown
# See also: https://api.slack.com/reference/surfaces/formatting#basics
def maybe_slack_to_markdown(content: str, translate_markdown: bool) -> str:
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


REDACT_PATTERNS = [
    (REDACT_EMAIL_PATTERN, "[EMAIL]"),
    (REDACT_CREDIT_CARD_PATTERN, "[CREDIT CARD]"),
    (REDACT_PHONE_PATTERN, "[PHONE]"),
    (REDACT_SSN_PATTERN, "[SSN]"),
    (REDACT_USER_DEFINED_PATTERN, "[REDACTED]"),
]


def maybe_redact_string(
    input_string: str,
    patterns: List[Tuple[str, str]],
    redaction_enabled: bool = True,
) -> str:
    """
    Optionally redact sensitive information from a string (inspired by @quangnhut123)

    Args:
        - input_string (str): The string to potentially redact
        - patterns (list[tuple]): A list of tuples where each tuple contains (regex pattern, replacement string)
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
        reply_text = maybe_slack_to_markdown(reply_text, TRANSLATE_MARKDOWN)
        content = [
            {
                "type": "text",
                "text": f"<@{reply['user'] if 'user' in reply else reply['username']}>: {reply_text}",
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


def should_ignore_message(
    *,
    context: BoltContext,
    payload: dict,
    client: WebClient,
) -> bool:
    """
    Check if the message should be ignored based on certain conditions.

    Args:
        context (BoltContext): The Bolt context object.
        payload (dict): The payload of the incoming message.
        client (WebClient): The Slack WebClient instance.
    Returns:
        bool: True if the message should be ignored, False otherwise.
    """
    if payload.get("bot_id") is not None:
        return True
    return (
        payload.get("channel_type") != "im"
        and not is_this_app_mentioned(context.bot_user_id, payload["text"])
        and not is_in_thread_started_by_app_mention(
            client, context, payload.get("thread_ts")
        )
    )


def post_loading_reply(
    *,
    client: WebClient,
    channel_id: str,
    payload: dict,
    loading_text: str,
) -> tuple[Optional[str], SlackResponse]:
    """
    Post a loading message to a channel or thread.

    Args:
        client (WebClient): Slack WebClient instance.
        channel_id (str): Channel ID to post the message to.
        payload (dict): Incoming message payload.
        loading_text (str): Message text to show while loading.
    Returns:
        tuple[Optional[str], SlackResponse]: Thread timestamp and Slack API response.
    """
    reply_thread_ts = payload.get("thread_ts")

    # If mentioned in a channel and outside a thread, reply in a thread
    if payload.get("channel_type") != "im" and reply_thread_ts is None:
        reply_thread_ts = payload["ts"]

    wip_reply = client.chat_postMessage(
        channel=channel_id,
        thread_ts=reply_thread_ts,
        text=loading_text,
    )
    return reply_thread_ts, wip_reply


def build_messages(
    *,
    client: WebClient,
    context: BoltContext,
    payload: dict,
    channel_id: str,
    user_id: str,
) -> list[dict]:
    messages = initialize_messages(SYSTEM_TEXT, context.bot_user_id, TRANSLATE_MARKDOWN)

    thread_ts = payload.get("thread_ts")
    # In the DM with the bot; this is not within a thread
    if payload.get("channel_type") == "im" and thread_ts is None:
        replies = get_dm_replies(client, channel_id)
    # Within a thread
    elif thread_ts is not None:
        replies = get_thread_replies(client, channel_id, thread_ts)
    # In a channel; mentioning the bot user outside a thread
    else:
        replies = [
            {
                "text": payload["text"],
                "user": user_id,
                "bot_id": payload.get("bot_id"),
                "files": payload.get("files"),
            }
        ]

    messages += convert_replies_to_messages(
        replies=replies,
        context=context,
        logger=client.logger,
    )
    messages, num_context_tokens, max_context_tokens = messages_within_context_window(
        messages
    )
    if len(messages) == 1:
        raise ContextOverflowError(num_context_tokens, max_context_tokens)

    if (
        ANTHROPIC_PROMPT_CACHING_ENABLED
        and num_context_tokens >= 1024
        and len([m for m in messages if m.get("role") == "user"]) > 1
    ):
        # Set cache points for the last two user messages
        user_messages_found = 0
        for message in reversed(messages):
            if message.get("role") == "user":
                message["content"][-1]["cache_control"] = {"type": "ephemeral"}
                user_messages_found += 1
                if user_messages_found >= 2:
                    break

    return messages


def handle_context_overflow(
    *,
    client: WebClient,
    channel_id: str,
    e: ContextOverflowError,
    wip_reply: Optional[SlackResponse],
) -> None:
    if wip_reply is None:
        return
    client.chat_update(
        channel=channel_id,
        ts=wip_reply["message"]["ts"],
        text=e.message,
    )


def handle_timeout_error(
    *,
    client: WebClient,
    channel_id: str,
    locale: Optional[str],
    wip_reply: Optional[SlackResponse],
):
    if wip_reply is None:
        return
    message_dict: dict = wip_reply.get("message", {})
    text = (
        message_dict.get("text", "")
        + "\n\n"
        + translate(locale=locale, text=TIMEOUT_ERROR_MESSAGE)
    )
    client.chat_update(
        channel=channel_id,
        ts=wip_reply["message"]["ts"],
        text=text,
    )


def handle_exception(
    *,
    client: WebClient,
    channel_id: str,
    e: Exception,
    wip_reply: Optional[SlackResponse],
):
    message_dict: dict = wip_reply.get("message", {}) if wip_reply else {}
    text = message_dict.get("text", "") + "\n\n" + f":warning: Failed to reply: {e}"
    client.logger.exception(text)
    if wip_reply:
        client.chat_update(
            channel=channel_id,
            ts=wip_reply["message"]["ts"],
            text=text,
        )


def respond_to_new_message(
    context: BoltContext,
    payload: dict,
    client: WebClient,
) -> None:
    """
    Respond to a new Slack message event.

    This function filters irrelevant messages, posts a loading message,
    builds the conversation history, and sends a response using a language model.

    Args:
        context (BoltContext): The Bolt context object.
        payload (dict): The payload of the incoming message.
        client (WebClient): The Slack WebClient instance.
    Returns:
        None
    """
    if context.channel_id is None:
        raise ValueError("context.channel_id cannot be None")

    user_id = extract_user_id_from_context(context)
    if user_id is None:
        raise ValueError("User ID could not be determined from context")

    wip_reply = None
    try:
        if should_ignore_message(context=context, payload=payload, client=client):
            return
        loading_text = translate(locale=context.get("locale"), text=LOADING_TEXT)
        reply_thread_ts, wip_reply = post_loading_reply(
            client=client,
            channel_id=context.channel_id,
            payload=payload,
            loading_text=loading_text,
        )
        messages = build_messages(
            client=client,
            context=context,
            payload=payload,
            channel_id=context.channel_id,
            user_id=user_id,
        )
        reply_to_slack_with_litellm(
            client=client,
            channel=context.channel_id,
            user_id=user_id,
            thread_ts=reply_thread_ts,
            messages=messages,
            loading_text=loading_text,
            wip_reply=wip_reply,
            timeout_seconds=LITELLM_TIMEOUT_SECONDS,
        )
    except ContextOverflowError as e:
        handle_context_overflow(
            client=client,
            channel_id=context.channel_id,
            e=e,
            wip_reply=wip_reply,
        )
    except (Timeout, TimeoutError):
        handle_timeout_error(
            client=client,
            channel_id=context.channel_id,
            locale=context.get("locale"),
            wip_reply=wip_reply,
        )
    except Exception as e:
        handle_exception(
            client=client,
            channel_id=context.channel_id,
            e=e,
            wip_reply=wip_reply,
        )
