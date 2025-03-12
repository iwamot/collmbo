import requests
from slack_sdk.errors import SlackApiError


def download_slack_image_content(image_url: str, bot_token: str) -> bytes:
    headers = {"Authorization": f"Bearer {bot_token}"}
    response = requests.get(image_url, headers=headers)
    if response.status_code != 200:
        error = f"Request to {image_url} failed with status code {response.status_code}"
        raise SlackApiError(error, response)

    content_type = response.headers.get("Content-Type", "")
    if content_type.startswith("text/html"):
        error = f"You don't have the permission to download this file: {image_url}"
        raise SlackApiError(error, response)

    if not content_type.startswith("image/"):
        error = f"The responded content-type is not for image data: {content_type}"
        raise SlackApiError(error, response)

    return response.content


def download_slack_pdf_content(pdf_url: str, bot_token: str) -> bytes:
    headers = {"Authorization": f"Bearer {bot_token}"}
    response = requests.get(pdf_url, headers=headers)
    if response.status_code != 200:
        error = f"Request to {pdf_url} failed with status code {response.status_code}"
        raise SlackApiError(error, response)

    content_type = response.headers.get("Content-Type", "")
    if content_type.startswith("text/html"):
        error = f"You don't have the permission to download this file: {pdf_url}"
        raise SlackApiError(error, response)

    if content_type not in ["application/pdf", "binary/octet-stream"]:
        error = f"The responded content-type is not for PDF data: {content_type}"
        raise SlackApiError(error, response)

    return response.content
