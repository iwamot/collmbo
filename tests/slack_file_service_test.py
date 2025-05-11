from unittest.mock import MagicMock

import pytest
from slack_sdk.errors import SlackApiError

from app.slack_file_service import download_slack_file_content


@pytest.mark.parametrize(
    "status_code, content_type, expected_content_types",
    [
        (200, "image/webp", ["image/png", "image/webp"]),
    ],
)
def test_download_slack_file_content_success(
    status_code, content_type, expected_content_types
):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = b"fake-content"

    def mock_http_get(url, headers):
        return mock_response

    content = download_slack_file_content(
        url="https://example.com/file",
        token="xoxb-fake-token",
        expected_content_types=expected_content_types,
        http_get=mock_http_get,
    )
    assert content == b"fake-content"


@pytest.mark.parametrize(
    "status_code, content_type, expected_content_types",
    [
        (403, "image/png", ["image/png"]),
        (200, "text/html", ["image/png"]),
        (200, "image/gif", ["image/png", "image/webp"]),
    ],
)
def test_download_slack_file_content_failure(
    status_code, content_type, expected_content_types
):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = {"Content-Type": content_type}
    mock_response.content = b"fake-content"

    def mock_http_get(url, headers):
        return mock_response

    with pytest.raises(SlackApiError):
        download_slack_file_content(
            url="https://example.com/file",
            token="xoxb-fake-token",
            expected_content_types=expected_content_types,
            http_get=mock_http_get,
        )
