import signal
from unittest.mock import ANY, MagicMock, patch

import pytest

from main import main, signal_handler


@pytest.fixture
def mock_slack_handler():
    return MagicMock()


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


def test_main(mock_slack_handler):
    with patch("signal.signal") as mock_signal, patch(
        "main.create_bolt_app"
    ) as mock_create_app:
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        def slack_handler_cls(app, token):
            return mock_slack_handler

        main(
            "test-bot-token",
            "test-app-token",
            slack_handler_cls=slack_handler_cls,
        )

        assert mock_signal.call_count == 2
        mock_signal.assert_any_call(signal.SIGTERM, ANY)
        mock_signal.assert_any_call(signal.SIGINT, ANY)

        mock_create_app.assert_called_once_with("test-bot-token")
        mock_slack_handler.start.assert_called_once()
