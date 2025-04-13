"""
This module contains utilities for direct Slack API interactions.
"""

import time
from typing import Optional

from slack_sdk.web import WebClient


def is_post_this_app_mentioned(
    bot_user_id: Optional[str], post: Optional[dict]
) -> bool:
    """
    Checks whether the bot is mentioned in a Slack post.

    Args:
        bot_user_id (Optional[str]): The bot's user ID.
        post (Optional[dict]): The Slack post.
    Returns:
        bool: True if the bot is mentioned, False otherwise.
    """
    return post is not None and f"<@{bot_user_id}>" in post.get("text", "")


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
