import pytest
from unittest.mock import MagicMock
from slack_bolt import BoltContext
from slack_sdk.web import WebClient
from app.bolt_middlewares import set_locale


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
