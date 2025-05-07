from typing import Callable

import requests
from slack_sdk.errors import SlackApiError


def download_slack_file_content(
    url: str,
    token: str,
    expected_content_types: list[str],
    http_get: Callable[..., requests.Response] = requests.get,
) -> bytes:
    headers = {"Authorization": f"Bearer {token}"}
    response = http_get(url, headers=headers)
    if response.status_code != 200:
        raise SlackApiError(
            f"Request to {url} failed with status code {response.status_code}", response
        )
    content_type = response.headers.get("Content-Type", "")
    if content_type.startswith("text/html"):
        raise SlackApiError(
            f"You don't have the permission to download this file: {url}", response
        )
    if content_type not in expected_content_types:
        raise SlackApiError(
            f"The responded content-type is not expected: {content_type}", response
        )
    return response.content
