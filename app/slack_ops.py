from typing import Optional
from urllib.request import Request, urlopen

from slack_bolt import BoltContext
from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse, WebClient

from app.env import IMAGE_FILE_ACCESS_ENABLED, PDF_FILE_ACCESS_ENABLED

# ----------------------------
# General operations in a channel
# ----------------------------


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


def is_this_app_mentioned(context: BoltContext, parent_message: dict) -> bool:
    parent_message_text = parent_message.get("text", "")
    return f"<@{context.bot_user_id}>" in parent_message_text


# ----------------------------
# WIP reply message stuff
# ----------------------------


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


# ----------------------------
# Files
# ----------------------------


def can_send_image_url_to_litellm(context: BoltContext) -> bool:
    if IMAGE_FILE_ACCESS_ENABLED is False:
        return False
    if context.authorize_result is None or context.authorize_result.bot_scopes is None:
        return False
    return "files:read" in context.authorize_result.bot_scopes


def download_slack_image_content(image_url: str, bot_token: str) -> bytes:
    request = Request(
        image_url,
        headers={"Authorization": f"Bearer {bot_token}"},
    )
    with urlopen(request) as response:
        if response.getcode() != 200:
            error = f"Request to {image_url} failed with status code {response.status}"
            raise SlackApiError(error, response)

        content_type = response.info().get("Content-Type")
        if content_type.startswith("text/html"):
            error = f"You don't have the permission to download this file: {image_url}"
            raise SlackApiError(error, response)

        if not content_type.startswith("image/"):
            error = f"The responded content-type is not for image data: {content_type}"
            raise SlackApiError(error, response)

        return response.read()


def can_send_pdf_url_to_litellm(context: BoltContext) -> bool:
    if PDF_FILE_ACCESS_ENABLED is False:
        return False
    if context.authorize_result is None or context.authorize_result.bot_scopes is None:
        return False
    return "files:read" in context.authorize_result.bot_scopes


def download_slack_pdf_content(pdf_url: str, bot_token: str) -> bytes:
    request = Request(
        pdf_url,
        headers={"Authorization": f"Bearer {bot_token}"},
    )
    with urlopen(request) as response:
        if response.getcode() != 200:
            error = f"Request to {pdf_url} failed with status code {response.status}"
            raise SlackApiError(error, response)

        content_type = response.info().get("Content-Type")
        if content_type.startswith("text/html"):
            error = f"You don't have the permission to download this file: {pdf_url}"
            raise SlackApiError(error, response)

        if content_type not in ["application/pdf", "binary/octet-stream"]:
            error = f"The responded content-type is not for PDF data: {content_type}"
            raise SlackApiError(error, response)

        return response.read()
