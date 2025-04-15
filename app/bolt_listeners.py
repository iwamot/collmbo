import time
from typing import Optional

from litellm.exceptions import Timeout
from slack_bolt import BoltContext
from slack_sdk.web import SlackResponse, WebClient

from app.bolt_logic import (
    determine_thread_ts_to_reply,
    extract_user_id_from_context,
    is_post_from_bot,
    is_post_in_dm,
    is_post_mentioned,
)
from app.env import LITELLM_TIMEOUT_SECONDS, PROMPT_CACHING_ENABLED
from app.i18n import translate
from app.litellm_ops import reply_to_slack_with_litellm, trim_messages_to_fit_context
from app.message_utils import build_system_message, convert_replies_to_messages

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

    if is_post_from_bot(payload):
        return

    wip_reply = None
    try:
        if not (
            is_post_mentioned(context.bot_user_id, payload)
            or is_post_in_dm(payload)
            or has_parent_post_mentioned(context, payload, client)
        ):
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


def has_parent_post_mentioned(
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
    parent_post = find_parent_post(
        client=client,
        channel_id=context.channel_id,
        thread_ts=payload.get("thread_ts"),
    )
    return is_post_mentioned(context.bot_user_id, parent_post)


def find_parent_post(
    client: WebClient, channel_id: Optional[str], thread_ts: Optional[str]
) -> Optional[dict]:
    """
    Finds the parent post of a thread in Slack.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (Optional[str]): The ID of the channel containing the thread.
        thread_ts (Optional[str]): The timestamp of the thread.

    Returns:
        Optional[dict]: The parent post if found, None otherwise.
    """
    if channel_id is None or thread_ts is None:
        return None
    posts: list[dict] = client.conversations_history(
        channel=channel_id,
        latest=thread_ts,
        limit=1,
        inclusive=True,
    ).get("messages", [])
    return posts[0] if posts else None


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
    thread_ts = determine_thread_ts_to_reply(payload)
    wip_reply = client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=loading_text,
    )
    return thread_ts, wip_reply


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


def get_replies(
    *,
    client: WebClient,
    payload: dict,
    channel_id: str,
    user_id: str,
) -> list[dict]:
    """
    Retrieves replies to be used as conversation history based on the context of the incoming Slack
    post.

    Args:
        client (WebClient): The Slack WebClient instance.
        payload (dict): The payload of the incoming Slack post.
        channel_id (str): The ID of the channel where the post was made.
        user_id (str): The ID of the user who made the post.

    Returns:
        list[dict]: A list of replies based on the post context.
    """
    thread_ts = payload.get("thread_ts")
    # In a DM with the bot (not part of a thread)
    if payload.get("channel_type") == "im" and thread_ts is None:
        return get_dm_replies(client, channel_id)
    # In a thread
    if thread_ts is not None:
        return get_thread_replies(client, channel_id, thread_ts)
    # In a channel (not in a thread), with a mention to the bot
    return [
        {
            "text": payload["text"],
            "user": user_id,
            "bot_id": payload.get("bot_id"),
            "files": payload.get("files"),
        }
    ]


def get_thread_replies(
    client: WebClient, channel_id: str, thread_ts: str
) -> list[dict]:
    """
    Retrieves all replies to a Slack thread.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the channel containing the thread.
        thread_ts (str): The timestamp of the parent post.

    Returns:
        list[dict]: A list of replies in the thread.
    """
    return client.conversations_replies(
        channel=channel_id,
        ts=thread_ts,
        limit=1000,
    ).get("messages", [])


def get_dm_replies(client: WebClient, channel_id: str) -> list[dict]:
    """
    Retrieves recent replies in a direct message (DM) conversation.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the DM channel.

    Returns:
        list[dict]: A list of replies in the DM conversation.
    """
    replies: list[dict] = client.conversations_history(
        channel=channel_id,
        limit=100,
        oldest=f"{time.time() - 86400:.6f}",  # 24 hours ago
        inclusive=True,
    ).get("messages", [])
    return list(reversed(replies))


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
