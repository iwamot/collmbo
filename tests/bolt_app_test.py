from unittest.mock import MagicMock, patch

from slack_bolt import App

from app.bolt_app import create_bolt_app, just_ack
from app.bolt_listeners import respond_to_app_mention, respond_to_new_message
from app.bolt_middlewares import set_locale


def test_just_ack():
    mock_ack = MagicMock()
    just_ack(ack=mock_ack)
    mock_ack.assert_called_once()


def test_create_bolt_app_with_locale():
    mock_slack_bot_token = "xoxb-12345-67890-abcde"
    mock_rate_limit_handler = MagicMock()

    with patch("app.bolt_app.App") as mock_app_class, patch(
        "app.bolt_app.RateLimitErrorRetryHandler", return_value=mock_rate_limit_handler
    ), patch("app.bolt_app.just_ack") as mock_just_ack, patch(
        "app.bolt_app.before_authorize"
    ) as mock_before_authorize:
        mock_app_instance = MagicMock(spec=App)
        mock_app_instance.client.retry_handlers = [mock_rate_limit_handler]
        mock_app_class.return_value = mock_app_instance

        app = create_bolt_app(
            slack_bot_token=mock_slack_bot_token, use_slack_language=True
        )

        assert app is mock_app_instance

        mock_app_class.assert_called_once_with(
            token=mock_slack_bot_token,
            before_authorize=mock_before_authorize,
            process_before_response=True,
        )

        assert mock_rate_limit_handler in mock_app_instance.client.retry_handlers

        mock_app_instance.event.assert_any_call("app_mention")
        mock_app_instance.event.assert_any_call("message")

        mock_app_instance.event("app_mention").assert_any_call(
            ack=mock_just_ack, lazy=[respond_to_app_mention]
        )
        mock_app_instance.event("message").assert_any_call(
            ack=mock_just_ack, lazy=[respond_to_new_message]
        )

        mock_app_instance.middleware.assert_called_once_with(set_locale)


def test_create_bolt_app_without_locale():
    mock_slack_bot_token = "xoxb-12345-67890-abcde"

    with patch("app.bolt_app.App") as mock_app_class:
        mock_app_instance = MagicMock(spec=App)
        mock_app_class.return_value = mock_app_instance

        create_bolt_app(slack_bot_token=mock_slack_bot_token, use_slack_language=False)

        mock_app_instance.middleware.assert_not_called()
