from typing import Optional

from litellm.exceptions import Timeout
from slack_bolt import BoltContext
from slack_sdk.web import SlackResponse, WebClient

from app.bolt_utils import extract_user_id_from_context
from app.env import LITELLM_TIMEOUT_SECONDS, PROMPT_CACHING_ENABLED
from app.i18n import translate
from app.litellm_ops import reply_to_slack_with_litellm, trim_messages_to_fit_context
from app.message_utils import build_system_message, convert_replies_to_messages
from app.slack_utils import (
    get_replies,
    is_in_thread_started_by_app_mention,
    is_this_app_mentioned,
)

TIMEOUT_ERROR_MESSAGE = (
    f":warning: Apologies! It seems that the AI didn't respond within the "
    f"{LITELLM_TIMEOUT_SECONDS}-second timeframe. Please try your request again later. "
    "If you wish to extend the timeout limit, you may consider deploying this app with "
    "customized settings on your infrastructure. :bow:"
)
LOADING_TEXT = ":hourglass_flowing_sand: Wait a second, please ..."


def respond_to_new_post(
    context: BoltContext,
    payload: dict,
    client: WebClient,
) -> None:
    """
    Responds to a new Slack post.

    This function filters irrelevant posts, posts a loading reply,
    builds the conversation history, and sends a response using a language model.

    Args:
        context (BoltContext): The Bolt context object.
        payload (dict): The payload of the incoming Slack post.
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
        if should_ignore_post(context, payload, client):
            return
        loading_text = translate(context.get("locale"), LOADING_TEXT)
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


def should_ignore_post(
    context: BoltContext,
    payload: dict,
    client: WebClient,
) -> bool:
    """
    Checks whether the Slack post should be ignored based on certain conditions.

    Args:
        context (BoltContext): The Bolt context object.
        payload (dict): The payload of the incoming Slack post.
        client (WebClient): The Slack WebClient instance.

    Returns:
        bool: True if the post should be ignored, False otherwise.
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
    Posts a loading reply to a Slack post in a channel or thread.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the channel to reply to.
        payload (dict): The payload of the incoming Slack post.
        loading_text (str): The loading text to display.

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
    system_message = build_system_message(context.bot_user_id)
    replies = get_replies(
        client=client,
        payload=payload,
        channel_id=channel_id,
        user_id=user_id,
    )
    messages = [system_message] + convert_replies_to_messages(
        replies, context, client.logger
    )
    messages, messages_tokens, tools_tokens = trim_messages_to_fit_context(messages)

    if (
        PROMPT_CACHING_ENABLED
        and messages_tokens + tools_tokens >= 1024
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
        message_dict.get("text", "") + "\n\n" + translate(locale, TIMEOUT_ERROR_MESSAGE)
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
