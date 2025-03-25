from typing import Optional

from slack_sdk.web import SlackResponse, WebClient


def post_wip_message(
    *,
    client: WebClient,
    channel: str,
    thread_ts: Optional[str],
    loading_text: str,
) -> SlackResponse:
    return client.chat_postMessage(
        channel=channel,
        thread_ts=thread_ts,
        text=loading_text,
    )


def update_wip_message(
    client: WebClient,
    channel: str,
    ts: str,
    text: str,
) -> SlackResponse:
    return client.chat_update(
        channel=channel,
        ts=ts,
        text=text,
    )
