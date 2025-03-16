import logging
from unittest.mock import MagicMock, patch

import pytest
from slack_bolt import BoltContext, BoltResponse
from slack_sdk.web import WebClient

from app.bolt_middlewares import before_authorize, set_locale


def test_before_authorize_skips_known_subtypes():
    mock_logger = MagicMock(spec=logging.Logger)
    mock_next = MagicMock()
    body = {"event": {}}
    payload = {"type": "message", "subtype": "message_changed"}

    with patch("app.bolt_middlewares.is_event", return_value=True):
        response = before_authorize(
            body=body, payload=payload, logger=mock_logger, next_=mock_next
        )
        assert isinstance(response, BoltResponse)
        assert response.status == 200
        assert response.body == ""
        mock_next.assert_not_called()


def test_before_authorize_calls_next_for_other_events():
    mock_logger = MagicMock(spec=logging.Logger)
    mock_next = MagicMock()
    body = {"event": {}}
    payload = {"type": "message", "subtype": "new_message"}

    with patch("app.bolt_middlewares.is_event", return_value=True):
        response = before_authorize(
            body=body, payload=payload, logger=mock_logger, next_=mock_next
        )
        assert response is None
        mock_next.assert_called_once()


def test_before_authorize_handles_non_message_events():
    mock_logger = MagicMock(spec=logging.Logger)
    mock_next = MagicMock()
    body = {"event": {}}
    payload = {"type": "other_event"}

    with patch("app.bolt_middlewares.is_event", return_value=True):
        response = before_authorize(
            body=body, payload=payload, logger=mock_logger, next_=mock_next
        )
        assert response is None
        mock_next.assert_called_once()


def test_before_authorize_handles_non_event_bodies():
    mock_logger = MagicMock(spec=logging.Logger)
    mock_next = MagicMock()
    body = {}
    payload = {"type": "message", "subtype": "message_changed"}

    with patch("app.bolt_middlewares.is_event", return_value=False):
        response = before_authorize(
            body=body, payload=payload, logger=mock_logger, next_=mock_next
        )
        assert response is None
        mock_next.assert_called_once()


@pytest.mark.parametrize(
    "user_info_response, expected_locale",
    [
        ({"user": {"locale": "ja-JP"}}, "ja-JP"),
        ({"user": {}}, None),
        ({}, None),
    ],
)
def test_set_locale_with_user_id(user_info_response, expected_locale):
    client_mock = MagicMock(spec=WebClient)
    client_mock.users_info.return_value = user_info_response

    context = BoltContext()
    context["user_id"] = "U123456"

    next_mock = MagicMock()

    set_locale(context, client_mock, next_mock)

    assert context["locale"] == expected_locale
    next_mock.assert_called_once()


def test_set_locale_without_user_id():
    client_mock = MagicMock(spec=WebClient)

    context = BoltContext()
    context["user_id"] = None

    next_mock = MagicMock()

    set_locale(context, client_mock, next_mock)

    assert context["locale"] is None
    next_mock.assert_called_once()
