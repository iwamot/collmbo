"""
This module contains utilities for direct Slack API interactions.
"""

from typing import Optional

from slack_bolt import BoltContext
from slack_sdk.web import WebClient


def is_this_app_mentioned(bot_user_id: Optional[str], text: str) -> bool:
    """
    Determines whether the bot is mentioned in a Slack message text.

    Args:
        bot_user_id (Optional[str]): The bot's user ID.
        text (str): The text to check for mentions.

    Returns:
        bool: True if the bot is mentioned in the text, False otherwise.
    """
    return f"<@{bot_user_id}>" in text


def find_parent_message(
    client: WebClient, channel_id: Optional[str], thread_ts: Optional[str]
) -> Optional[dict]:
    """
    Finds the parent message of a thread.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (Optional[str]): The ID of the channel containing the thread.
        thread_ts (Optional[str]): The timestamp of the thread.

    Returns:
        Optional[dict]: The parent message if found, None otherwise.
    """
    if channel_id is None or thread_ts is None:
        return None

    messages: list[dict] = client.conversations_history(
        channel=channel_id,
        latest=thread_ts,
        limit=1,
        inclusive=True,
    ).get("messages", [])

    return messages[0] if messages else None


def is_in_thread_started_by_app_mention(
    client: WebClient,
    context: BoltContext,
    thread_ts: Optional[str],
) -> bool:
    """
    Determines if the current message is in a thread that was started by mentioning the app.

    Args:
        client (WebClient): The Slack WebClient instance.
        context (BoltContext): The Bolt context object.
        thread_ts (Optional[str]): The timestamp of the thread.

    Returns:
        bool: True if the message is in a thread started by app mention, False otherwise.
    """
    if context.channel_id is None or thread_ts is None:
        return False
    parent_message = find_parent_message(client, context.channel_id, thread_ts)
    return parent_message is not None and is_this_app_mentioned(
        context.bot_user_id, parent_message.get("text", "")
    )
