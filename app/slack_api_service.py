from typing import Optional

from slack_sdk.web import SlackResponse, WebClient


class SlackApiService:
    """
    Service class for Slack API operations.
    Provides methods for finding parent messages, posting and updating messages in Slack.
    """

    def __init__(self, client: WebClient):
        """
        Initialize the SlackApiService.

        Args:
            client: The Slack WebClient instance
        """
        self.client = client

    def find_parent_message(
        self, channel: Optional[str], thread_ts: Optional[str]
    ) -> Optional[dict]:
        """
        Find the parent message in a thread.

        Args:
            channel: The Slack channel ID
            thread_ts: Timestamp of the thread

        Returns:
            The parent message as a dict, or None if not found
        """
        if channel is None or thread_ts is None:
            return None

        messages: list[dict] = self.client.conversations_history(
            channel=channel,
            latest=thread_ts,
            limit=1,
            inclusive=True,
        ).get("messages", [])

        return messages[0] if messages else None

    def post_wip_message(
        self,
        channel: str,
        thread_ts: Optional[str],
        loading_text: str,
        messages: list[dict],
        user: str,
    ) -> SlackResponse:
        """
        Post a "work in progress" message to Slack.

        Args:
            channel: The Slack channel ID
            thread_ts: Optional timestamp of the thread
            loading_text: The text to display while loading
            messages: List of message dicts
            user: The user ID

        Returns:
            The Slack response
        """
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        return self.client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=loading_text,
            metadata={
                "event_type": "litellm-convo",
                "event_payload": {"messages": system_messages, "user": user},
            },
        )

    def update_wip_message(
        self,
        channel: str,
        ts: str,
        text: str,
        messages: list[dict],
        user: str,
    ) -> SlackResponse:
        """
        Update an existing "work in progress" message in Slack.

        Args:
            channel: The Slack channel ID
            ts: The timestamp of the message to update
            text: The new text for the message
            messages: List of message dicts
            user: The user ID

        Returns:
            The Slack response
        """
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        return self.client.chat_update(
            channel=channel,
            ts=ts,
            text=text,
            metadata={
                "event_type": "litellm-convo",
                "event_payload": {"messages": system_messages, "user": user},
            },
        )
