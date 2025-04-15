"""
This module is the entry point for Collmbo, the Slack chatbot.

It initializes the Slack Bolt app, sets up signal handlers for graceful shutdown,
and starts the Socket Mode handler.
"""

import logging
import os
import signal
import sys
from types import FrameType
from typing import Optional

from slack_bolt import Ack, App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.bolt_listeners import respond_to_new_post
from app.bolt_logic import append_rate_limit_retry_handler
from app.bolt_middlewares import before_authorize, set_locale
from app.env import SLACK_APP_LOG_LEVEL, USE_SLACK_LANGUAGE


def main() -> None:
    """
    Main entry point for Collmbo, the Slack chatbot application.

    Args:
        slack_bot_token (str): The Slack bot token for authentication.
        slack_app_token (str): The Slack app token for Socket Mode.

    Returns:
        None
    """
    logging.basicConfig(level=SLACK_APP_LOG_LEVEL)
    app = create_bolt_app(os.environ["SLACK_BOT_TOKEN"], USE_SLACK_LANGUAGE)
    append_rate_limit_retry_handler(app.client.retry_handlers, 2)
    slack_handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    register_signal_handlers(slack_handler)
    slack_handler.start()


def create_bolt_app(slack_bot_token: str, use_slack_language: bool) -> App:
    """
    Create and configure a Slack Bolt app instance.

    Args:
        slack_bot_token (str): The Slack bot token for authentication.

    Returns:
        App: The configured Slack Bolt app instance.
    """
    app = App(
        token=slack_bot_token,
        before_authorize=before_authorize,
        process_before_response=True,
    )
    app.event("message")(ack=just_ack, lazy=[respond_to_new_post])
    if use_slack_language:
        app.middleware(set_locale)
    return app


def just_ack(ack: Ack) -> None:
    """
    A simple acknowledgment function that does nothing.

    This is used as a placeholder for the ack parameter in Slack Bolt events.

    Args:
        ack (Ack): The acknowledgment function provided by Slack Bolt.

    Returns:
        None
    """
    ack()


def register_signal_handlers(slack_handler: SocketModeHandler) -> None:
    """
    Register signal handlers for graceful shutdown.

    Args:
        slack_handler (SocketModeHandler): The active SocketModeHandler instance to shut down.

    Returns:
        None
    """

    def handler(signum: int, _: Optional[FrameType]) -> None:
        logging.getLogger(__name__).info(
            "Received %s, shutting down...", signal.Signals(signum).name
        )
        try:
            slack_handler.close()
        except Exception:
            pass
        sys.exit(0)

    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, handler)


if __name__ == "__main__":
    main()
