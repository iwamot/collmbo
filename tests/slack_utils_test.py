import time
from unittest.mock import MagicMock, patch

import pytest
from slack_bolt import BoltContext
from slack_sdk.web import WebClient

from app.slack_utils import (
    find_parent_post,
    get_dm_replies,
    get_replies,
    get_thread_replies,
    is_in_thread_started_by_app_mention,
    is_this_app_mentioned,
)


@pytest.fixture
def mock_client():
    return MagicMock(spec=WebClient)


@pytest.fixture
def mock_context():
    context = MagicMock(spec=BoltContext)
    context.channel_id = "C12345678"
    context.bot_user_id = "U87654321"
    return context


@pytest.mark.parametrize(
    "bot_user_id, text, expected",
    [
        ("U12345", "Hello <@U12345>", True),
        ("U12345", "No mention here", False),
        (None, "Hello <@U12345>", False),
    ],
)
def test_is_this_app_mentioned(bot_user_id, text, expected):
    assert is_this_app_mentioned(bot_user_id, text) == expected


def test_find_parent_post_with_valid_response():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {
        "messages": [{"text": "Hello, world!"}]
    }

    result = find_parent_post(mock_client, "C12345678", "123456.789")
    assert result == {"text": "Hello, world!"}


def test_find_parent_post_with_no_messages():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {"messages": []}

    result = find_parent_post(mock_client, "C12345678", "123456.789")
    assert result is None


def test_find_parent_post_with_none_channel_id():
    mock_client = MagicMock(spec=WebClient)

    result = find_parent_post(mock_client, None, "123456.789")
    assert result is None


def test_find_parent_post_with_none_thread_ts():
    mock_client = MagicMock(spec=WebClient)

    result = find_parent_post(mock_client, "C12345678", None)
    assert result is None


def test_find_parent_post_with_invalid_response():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {"not_messages": []}

    result = find_parent_post(mock_client, "C12345678", "123456.789")
    assert result is None


@patch("app.slack_utils.find_parent_post", return_value=None)
@patch("app.slack_utils.is_this_app_mentioned")
def test_is_in_thread_started_by_app_mention_no_channel_id(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    mock_context.channel_id = None
    assert (
        is_in_thread_started_by_app_mention(mock_client, mock_context, "12345") is False
    )
    mock_find_parent.assert_not_called()
    mock_is_mentioned.assert_not_called()


@patch("app.slack_utils.find_parent_post", return_value=None)
@patch("app.slack_utils.is_this_app_mentioned")
def test_is_in_thread_started_by_app_mention_no_thread_ts(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert is_in_thread_started_by_app_mention(mock_client, mock_context, None) is False
    mock_find_parent.assert_not_called()
    mock_is_mentioned.assert_not_called()


@patch("app.slack_utils.find_parent_post", return_value=None)
@patch("app.slack_utils.is_this_app_mentioned")
def test_is_in_thread_started_by_app_mention_no_parent_message(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert (
        is_in_thread_started_by_app_mention(mock_client, mock_context, "12345") is False
    )
    mock_find_parent.assert_called_once_with(
        mock_client, mock_context.channel_id, "12345"
    )
    mock_is_mentioned.assert_not_called()


@patch("app.slack_utils.find_parent_post", return_value={"text": "Hello"})
@patch("app.slack_utils.is_this_app_mentioned", return_value=False)
def test_is_in_thread_started_by_app_mention_not_mentioned(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert (
        is_in_thread_started_by_app_mention(mock_client, mock_context, "12345") is False
    )
    mock_find_parent.assert_called_once_with(
        mock_client, mock_context.channel_id, "12345"
    )
    mock_is_mentioned.assert_called_once_with(mock_context.bot_user_id, "Hello")


@patch(
    "app.slack_utils.find_parent_post",
    return_value={"text": "Hello <@U87654321>"},
)
@patch("app.slack_utils.is_this_app_mentioned", return_value=True)
def test_is_in_thread_started_by_app_mention_true(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert (
        is_in_thread_started_by_app_mention(mock_client, mock_context, "12345") is True
    )
    mock_find_parent.assert_called_once_with(
        mock_client, mock_context.channel_id, "12345"
    )
    mock_is_mentioned.assert_called_once_with(
        mock_context.bot_user_id, "Hello <@U87654321>"
    )


def test_get_thread_replies_returns_messages(mock_client):
    mock_client.conversations_replies.return_value = {
        "messages": [
            {"text": "Reply 1"},
            {"text": "Reply 2"},
        ]
    }

    result = get_thread_replies(mock_client, "C12345678", "12345.6789")
    assert result == [
        {"text": "Reply 1"},
        {"text": "Reply 2"},
    ]
    mock_client.conversations_replies.assert_called_once_with(
        channel="C12345678",
        ts="12345.6789",
        limit=1000,
    )


def test_get_thread_replies_returns_empty_when_no_messages_key(mock_client):
    mock_client.conversations_replies.return_value = {}

    result = get_thread_replies(mock_client, "C12345678", "12345.6789")
    assert result == []


def test_get_dm_replies_returns_reversed_messages(mock_client):
    mock_client.conversations_history.return_value = {
        "messages": [
            {"text": "Oldest"},
            {"text": "Newest"},
        ]
    }

    result = get_dm_replies(mock_client, "D12345678")
    assert result == [
        {"text": "Newest"},
        {"text": "Oldest"},
    ]
    mock_client.conversations_history.assert_called_once()
    args, kwargs = mock_client.conversations_history.call_args
    assert kwargs["channel"] == "D12345678"
    assert kwargs["limit"] == 100
    assert kwargs["inclusive"] is True
    assert float(kwargs["oldest"]) < time.time()


def test_get_dm_replies_returns_empty_when_no_messages_key(mock_client):
    mock_client.conversations_history.return_value = {}

    result = get_dm_replies(mock_client, "D12345678")
    assert result == []


@patch("app.slack_utils.get_dm_replies", return_value=[{"text": "DM message"}])
def test_get_replies_returns_dm_replies(mock_get_dm, mock_client):
    payload = {
        "channel_type": "im",
        "text": "Hello",
        "thread_ts": None,
        "bot_id": None,
        "files": [],
    }
    result = get_replies(
        client=mock_client,
        payload=payload,
        channel_id="D12345678",
        user_id="U12345678",
    )
    assert result == [{"text": "DM message"}]
    mock_get_dm.assert_called_once_with(mock_client, "D12345678")


@patch("app.slack_utils.get_thread_replies", return_value=[{"text": "Thread reply"}])
def test_get_replies_returns_thread_replies(mock_get_thread, mock_client):
    payload = {
        "channel_type": "channel",
        "thread_ts": "12345.6789",
        "text": "Hello",
        "bot_id": None,
        "files": [],
    }
    result = get_replies(
        client=mock_client,
        payload=payload,
        channel_id="C12345678",
        user_id="U12345678",
    )
    assert result == [{"text": "Thread reply"}]
    mock_get_thread.assert_called_once_with(mock_client, "C12345678", "12345.6789")


def test_get_replies_returns_single_message_for_top_level(mock_client):
    payload = {
        "channel_type": "channel",
        "thread_ts": None,
        "text": "Top-level message",
        "bot_id": "B123456",
        "files": ["file1"],
    }
    result = get_replies(
        client=mock_client,
        payload=payload,
        channel_id="C12345678",
        user_id="U12345678",
    )
    assert result == [
        {
            "text": "Top-level message",
            "user": "U12345678",
            "bot_id": "B123456",
            "files": ["file1"],
        }
    ]
