from typing import Optional

from slack_sdk.web import SlackResponse, WebClient


def post_wip_message(
    *,
    client: WebClient,
    channel: str,
    thread_ts: Optional[str],
    loading_text: str,
    messages: list[dict],
    user: str,
) -> SlackResponse:
    system_messages = [msg for msg in messages if msg["role"] == "system"]
    return client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=loading_text,
        metadata={
            "event_type": "litellm-convo",
            "event_payload": {"messages": system_messages, "user": user},
        },
    )


def update_wip_message(
    client: WebClient,
    channel: str,
    ts: str,
    text: str,
    messages: list[dict],
    user: str,
) -> SlackResponse:
    system_messages = [msg for msg in messages if msg["role"] == "system"]
    return client.chat_update(
        channel=channel,
        ts=ts,
        text=text,
        metadata={
            "event_type": "litellm-convo",
            "event_payload": {"messages": system_messages, "user": user},
        },
    )
