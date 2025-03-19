from unittest.mock import MagicMock

from slack_sdk.web import SlackResponse, WebClient

from app.slack_wip_message import post_wip_message, update_wip_message


def test_post_wip_message_including_user_messages():
    mock_client = MagicMock(spec=WebClient)
    mock_response = MagicMock(spec=SlackResponse)
    mock_client.chat_postMessage.return_value = mock_response

    response = post_wip_message(
        client=mock_client,
        channel="C12345678",
        thread_ts="123456.789",
        loading_text="Loading...",
        messages=[
            {"role": "system", "content": "System message 1"},
            {"role": "user", "content": "User message 1"},
            {"role": "system", "content": "System message 2"},
            {"role": "user", "content": "User message 2"},
        ],
        user="U12345678",
    )

    mock_client.chat_postMessage.assert_called_once_with(
        channel="C12345678",
        thread_ts="123456.789",
        text="Loading...",
        metadata={
            "event_type": "collmbo-convo",
            "event_payload": {
                "messages": [
                    {"role": "system", "content": "System message 1"},
                    {"role": "system", "content": "System message 2"},
                ],
                "user": "U12345678",
            },
        },
    )
    assert response == mock_response


def test_update_wip_message_including_user_messages():
    mock_client = MagicMock(spec=WebClient)
    mock_response = MagicMock(spec=SlackResponse)
    mock_client.chat_update.return_value = mock_response

    response = update_wip_message(
        client=mock_client,
        channel="C12345678",
        ts="123456.789",
        text="Updated message",
        messages=[
            {"role": "system", "content": "Updated system message 1"},
            {"role": "user", "content": "User message 1"},
            {"role": "system", "content": "Updated system message 2"},
            {"role": "user", "content": "User message 2"},
        ],
        user="U12345678",
    )

    mock_client.chat_update.assert_called_once_with(
        channel="C12345678",
        ts="123456.789",
        text="Updated message",
        metadata={
            "event_type": "collmbo-convo",
            "event_payload": {
                "messages": [
                    {"role": "system", "content": "Updated system message 1"},
                    {"role": "system", "content": "Updated system message 2"},
                ],
                "user": "U12345678",
            },
        },
    )
    assert response == mock_response
