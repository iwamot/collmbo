import logging
import re
import time
from typing import List, Optional, Sequence, Tuple

from litellm.exceptions import Timeout
from slack_bolt import BoltContext
from slack_sdk.web import SlackResponse, WebClient

from app.env import (
    IMAGE_FILE_ACCESS_ENABLED,
    LITELLM_TEMPERATURE,
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
from app.i18n import translate
from app.litellm_image_ops import get_image_content_if_exists
from app.litellm_ops import (
    consume_litellm_stream_to_write_reply,
    messages_within_context_window,
    start_receiving_litellm_response,
)
from app.litellm_pdf_ops import get_pdf_content_if_exists, trim_pdf_content
from app.slack_wip_message import post_wip_message, update_wip_message

TIMEOUT_ERROR_MESSAGE = (
    f":warning: Apologies! It seems that the AI didn't respond within the {LITELLM_TIMEOUT_SECONDS}-second timeframe. "
    "Please try your request again later. "
    "If you wish to extend the timeout limit, "
    "you may consider deploying this app with customized settings on your infrastructure. :bow:"
)
LOADING_TEXT = ":hourglass_flowing_sand: Wait a second, please ..."


def find_parent_message(
    client: WebClient, channel_id: Optional[str], thread_ts: Optional[str]
) -> Optional[dict]:
    if channel_id is None or thread_ts is None:
        return None

    messages: list[dict] = client.conversations_history(
        channel=channel_id,
        latest=thread_ts,
        limit=1,
        inclusive=True,
    ).get("messages", [])

    return messages[0] if messages else None


def is_this_app_mentioned(bot_user_id: Optional[str], parent_message: dict) -> bool:
    parent_message_text = parent_message.get("text", "")
    return f"<@{bot_user_id}>" in parent_message_text


def is_child_message_and_mentioned(
    client: WebClient,
    context: BoltContext,
    thread_ts: Optional[str],
) -> bool:
    if context.channel_id is None or thread_ts is None:
        return False
    parent_message = find_parent_message(client, context.channel_id, thread_ts)
    return parent_message is not None and is_this_app_mentioned(
        context.bot_user_id, parent_message
    )


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
        oldest="%.6f" % (time.time() - 86400),  # 24 hours ago
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

    for reply in replies:
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
        if (
            reply.get("bot_id") is None
            and context.authorize_result is not None
            and PDF_FILE_ACCESS_ENABLED
            and can_bot_read_files(context.authorize_result.bot_scopes)
        ):
            if context.bot_token is None:
                raise ValueError("context.bot_token cannot be None")
            content += get_pdf_content_if_exists(
                bot_token=context.bot_token,
                files=reply.get("files"),
                logger=logger,
            )

        messages.append({"role": "user", "content": content})

    trim_pdf_content(messages)
    return messages


def reply_to_messages(
    *,
    messages: list[dict],
    user_id: str,
    thread_ts: str,
    loading_text: str,
    channel_id: str,
    client: WebClient,
    logger: logging.Logger,
    wip_reply: SlackResponse,
) -> None:
    messages, num_context_tokens, max_context_tokens = messages_within_context_window(
        messages
    )

    if len(messages) == 1:
        update_wip_message(
            client=client,
            channel=channel_id,
            ts=wip_reply["message"]["ts"],
            text=(
                f":warning: The previous message is too long "
                f"({num_context_tokens}/{max_context_tokens} prompt tokens)."
            ),
        )
        return

    stream = start_receiving_litellm_response(
        temperature=LITELLM_TEMPERATURE,
        messages=messages,
        user=user_id,
    )
    consume_litellm_stream_to_write_reply(
        client=client,
        wip_reply=wip_reply,
        channel=channel_id,
        user_id=user_id,
        messages=messages,
        stream=stream,
        thread_ts=thread_ts,
        loading_text=loading_text,
        timeout_seconds=LITELLM_TIMEOUT_SECONDS,
        translate_markdown=TRANSLATE_MARKDOWN,
        logger=logger,
    )


def handle_timeout_error(
    channel_id: str,
    locale: Optional[str],
    wip_reply: Optional[SlackResponse],
    client: WebClient,
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
    e: Exception,
    channel_id: str,
    wip_reply: Optional[SlackResponse],
    client: WebClient,
    logger: logging.Logger,
):
    message_dict: dict = wip_reply.get("message", {}) if wip_reply else {}
    text = message_dict.get("text", "") + "\n\n" + f":warning: Failed to reply: {e}"
    logger.exception(text)
    if wip_reply:
        client.chat_update(
            channel=channel_id,
            ts=wip_reply["message"]["ts"],
            text=text,
        )


def respond_to_app_mention(
    context: BoltContext,
    payload: dict,
    client: WebClient,
    logger: logging.Logger,
):
    if context.channel_id is None:
        raise ValueError("context.channel_id cannot be None")

    user_id = context.actor_user_id or context.user_id
    if user_id is None:
        raise ValueError("user_id cannot be None")

    thread_ts = payload.get("thread_ts")
    if is_child_message_and_mentioned(client, context, thread_ts):
        # The message event handler will reply to this
        return

    messages: list[dict] = initialize_messages(
        SYSTEM_TEXT, context.bot_user_id, TRANSLATE_MARKDOWN
    )

    wip_reply = None
    try:
        loading_text = translate(locale=context.get("locale"), text=LOADING_TEXT)
        wip_reply = post_wip_message(
            client=client,
            channel=context.channel_id,
            thread_ts=payload["ts"],
            loading_text=loading_text,
        )

        if thread_ts is not None:
            # Mentioning the bot user in a thread
            replies = get_thread_replies(
                client=client,
                channel=context.channel_id,
                thread_ts=thread_ts,
            )
        else:
            # Mentioning the bot user outside a thread
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
            logger=logger,
        )
        reply_to_messages(
            messages=messages,
            user_id=user_id,
            thread_ts=payload["ts"],
            loading_text=loading_text,
            channel_id=context.channel_id,
            client=client,
            logger=logger,
            wip_reply=wip_reply,
        )

    except (Timeout, TimeoutError):
        handle_timeout_error(
            channel_id=context.channel_id,
            locale=context.get("locale"),
            wip_reply=wip_reply,
            client=client,
        )
    except Exception as e:
        handle_exception(e, context.channel_id, wip_reply, client, logger)


def respond_to_new_message(
    context: BoltContext,
    payload: dict,
    client: WebClient,
    logger: logging.Logger,
):
    if context.channel_id is None:
        raise ValueError("context.channel_id cannot be None")

    user_id = context.actor_user_id or context.user_id
    if user_id is None:
        raise ValueError("user_id cannot be None")

    if payload.get("bot_id") is not None:
        return

    messages: list[dict] = initialize_messages(
        SYSTEM_TEXT, context.bot_user_id, TRANSLATE_MARKDOWN
    )

    wip_reply = None
    try:
        is_in_dm_with_bot = payload.get("channel_type") == "im"
        thread_ts = payload.get("thread_ts")

        # In the DM with the bot; this is not within a thread
        if is_in_dm_with_bot and thread_ts is None:
            replies = get_dm_replies(client, context.channel_id)
        # Within a thread
        elif thread_ts is not None:
            replies = get_thread_replies(
                client=client,
                channel=context.channel_id,
                thread_ts=thread_ts,
            )
            if not is_in_dm_with_bot:
                # In a channel
                parent_message = next(
                    (msg for msg in replies if msg.get("ts") == thread_ts),
                    None,
                )
                if parent_message is None:
                    parent_message = find_parent_message(
                        client, context.channel_id, thread_ts
                    )
                if parent_message is None or not is_this_app_mentioned(
                    context.bot_user_id, parent_message
                ):
                    return
        else:
            return

        loading_text = translate(locale=context.get("locale"), text=LOADING_TEXT)
        if not is_in_dm_with_bot:
            thread_ts = payload["ts"]
        wip_reply = post_wip_message(
            client=client,
            channel=context.channel_id,
            thread_ts=thread_ts,
            loading_text=loading_text,
        )

        messages += convert_replies_to_messages(
            replies=replies,
            context=context,
            logger=logger,
        )
        reply_to_messages(
            messages=messages,
            user_id=user_id,
            thread_ts=thread_ts,
            loading_text=loading_text,
            channel_id=context.channel_id,
            client=client,
            logger=logger,
            wip_reply=wip_reply,
        )

    except (Timeout, TimeoutError):
        handle_timeout_error(
            channel_id=context.channel_id,
            locale=context.get("locale"),
            wip_reply=wip_reply,
            client=client,
        )
    except Exception as e:
        handle_exception(e, context.channel_id, wip_reply, client, logger)
