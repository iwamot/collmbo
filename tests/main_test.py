import signal
from unittest.mock import ANY, MagicMock, patch

import pytest
from slack_bolt import App

from app.bolt_listeners import respond_to_new_post
from app.bolt_middlewares import set_locale
from main import (
    create_bolt_app,
    just_ack,
    main,
    make_signal_handler,
    register_signal_handlers,
    signal_handler,
)


@pytest.fixture
def mock_slack_handler():
    return MagicMock()


def test_main(mock_slack_handler):
    with patch("signal.signal") as mock_signal, patch(
        "main.create_bolt_app"
    ) as mock_create_app, patch("main.SocketModeHandler") as mock_handler_class:
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        mock_handler_class.return_value = mock_slack_handler

        main("test-bot-token", "test-app-token")

        assert mock_signal.call_count == 2
        mock_signal.assert_any_call(signal.SIGTERM, ANY)
        mock_signal.assert_any_call(signal.SIGINT, ANY)

        mock_create_app.assert_called_once_with("test-bot-token")
        mock_handler_class.assert_called_once_with(mock_app, "test-app-token")
        mock_slack_handler.start.assert_called_once()


def test_create_bolt_app_with_locale():
    mock_slack_bot_token = "xoxb-12345-67890-abcde"
    mock_rate_limit_handler = MagicMock()

    with patch("main.App") as mock_app_class, patch(
        "main.USE_SLACK_LANGUAGE", True
    ), patch(
        "main.RateLimitErrorRetryHandler", return_value=mock_rate_limit_handler
    ), patch(
        "main.just_ack"
    ) as mock_just_ack, patch(
        "main.before_authorize"
    ) as mock_before_authorize:
        mock_app_instance = MagicMock(spec=App)
        mock_app_instance.client.retry_handlers = [mock_rate_limit_handler]
        mock_app_class.return_value = mock_app_instance

        app = create_bolt_app(slack_bot_token=mock_slack_bot_token)

        assert app is mock_app_instance

        mock_app_class.assert_called_once_with(
            token=mock_slack_bot_token,
            before_authorize=mock_before_authorize,
            process_before_response=True,
        )

        assert mock_rate_limit_handler in mock_app_instance.client.retry_handlers

        mock_app_instance.event.assert_any_call("message")

        mock_app_instance.event("message").assert_any_call(
            ack=mock_just_ack, lazy=[respond_to_new_post]
        )

        mock_app_instance.middleware.assert_called_once_with(set_locale)


def test_create_bolt_app_without_locale():
    mock_slack_bot_token = "xoxb-12345-67890-abcde"

    with patch("main.App") as mock_app_class, patch("main.USE_SLACK_LANGUAGE", False):
        mock_app_instance = MagicMock(spec=App)
        mock_app_class.return_value = mock_app_instance

        create_bolt_app(slack_bot_token=mock_slack_bot_token)

        mock_app_instance.middleware.assert_not_called()


def test_just_ack():
    mock_ack = MagicMock()
    just_ack(ack=mock_ack)
    mock_ack.assert_called_once()


def test_signal_handler_success(mock_slack_handler):
    with patch("sys.exit") as mock_exit:
        signal_handler(signal.SIGTERM, None, mock_slack_handler)
        mock_slack_handler.close.assert_called_once()
        mock_exit.assert_called_once()


def test_signal_handler_exception(mock_slack_handler):
    mock_slack_handler.close.side_effect = RuntimeError("Test Exception")
    with patch("sys.exit") as mock_exit:
        signal_handler(signal.SIGTERM, None, mock_slack_handler)
        mock_slack_handler.close.assert_called_once()
        mock_exit.assert_called_once()


def test_make_signal_handler(mock_slack_handler):
    with patch("main.signal_handler") as mock_signal_handler:
        handler = make_signal_handler(mock_slack_handler)
        handler(signal.SIGTERM, None)
        mock_signal_handler.assert_called_once_with(
            signal.SIGTERM, None, mock_slack_handler
        )


def test_register_signal_handlers(mock_slack_handler):
    with patch("signal.signal") as mock_signal:
        register_signal_handlers(mock_slack_handler)

        assert mock_signal.call_count == 2
        mock_signal.assert_any_call(signal.SIGTERM, ANY)
        mock_signal.assert_any_call(signal.SIGINT, ANY)
