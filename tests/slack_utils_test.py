from unittest.mock import MagicMock, patch

import pytest
from slack_bolt import BoltContext
from slack_sdk.web import WebClient

from app.slack_utils import (
    find_parent_message,
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


def test_find_parent_message_with_valid_response():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {
        "messages": [{"text": "Hello, world!"}]
    }

    result = find_parent_message(mock_client, "C12345678", "123456.789")
    assert result == {"text": "Hello, world!"}


def test_find_parent_message_with_no_messages():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {"messages": []}

    result = find_parent_message(mock_client, "C12345678", "123456.789")
    assert result is None


def test_find_parent_message_with_none_channel_id():
    mock_client = MagicMock(spec=WebClient)

    result = find_parent_message(mock_client, None, "123456.789")
    assert result is None


def test_find_parent_message_with_none_thread_ts():
    mock_client = MagicMock(spec=WebClient)

    result = find_parent_message(mock_client, "C12345678", None)
    assert result is None


def test_find_parent_message_with_invalid_response():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {"not_messages": []}

    result = find_parent_message(mock_client, "C12345678", "123456.789")
    assert result is None


@patch("app.slack_utils.find_parent_message", return_value=None)
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


@patch("app.slack_utils.find_parent_message", return_value=None)
@patch("app.slack_utils.is_this_app_mentioned")
def test_is_in_thread_started_by_app_mention_no_thread_ts(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert is_in_thread_started_by_app_mention(mock_client, mock_context, None) is False
    mock_find_parent.assert_not_called()
    mock_is_mentioned.assert_not_called()


@patch("app.slack_utils.find_parent_message", return_value=None)
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


@patch("app.slack_utils.find_parent_message", return_value={"text": "Hello"})
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
    "app.slack_utils.find_parent_message",
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
