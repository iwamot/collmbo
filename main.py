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
from typing import Callable, Optional

from slack_bolt import Ack, App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from app.bolt_listeners import respond_to_new_post
from app.bolt_middlewares import before_authorize, set_locale
from app.env import SLACK_APP_LOG_LEVEL, USE_SLACK_LANGUAGE


def main(slack_bot_token: str, slack_app_token: str) -> None:
    """
    Main entry point for Collmbo, the Slack chatbot application.

    Args:
        slack_bot_token (str): The Slack bot token for authentication.
        slack_app_token (str): The Slack app token for Socket Mode.

    Returns:
        None
    """
    logging.basicConfig(level=SLACK_APP_LOG_LEVEL)
    app = create_bolt_app(slack_bot_token)
    slack_handler = SocketModeHandler(app, slack_app_token)
    register_signal_handlers(slack_handler)
    slack_handler.start()


def create_bolt_app(slack_bot_token: str) -> App:
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
    app.client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=2))
    app.event("message")(ack=just_ack, lazy=[respond_to_new_post])
    if USE_SLACK_LANGUAGE:
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


def signal_handler(
    signum: int, _: Optional[FrameType], slack_handler: SocketModeHandler
) -> None:
    """
    Handle termination signals for graceful shutdown.

    Args:
        signum (int): The signal number received.
        _ (Optional[FrameType]): The current stack frame. Not used.
        slack_handler (SocketModeHandler): The active SocketModeHandler instance to shut down.

    Returns:
        None
    """
    logging.getLogger(__name__).info(
        "Received %s, shutting down...", signal.Signals(signum).name
    )
    try:
        slack_handler.close()
    except Exception:
        pass
    sys.exit(0)


def make_signal_handler(
    slack_handler: SocketModeHandler,
) -> Callable[[int, Optional[FrameType]], None]:
    """
    Create a signal handler for graceful shutdown.

    Args:
        slack_handler (SocketModeHandler): The active SocketModeHandler instance to shut down.

    Returns:
        Callable[[int, Optional[FrameType]], None]: A function that handles signals.
    """
    return lambda signum, frame: signal_handler(signum, frame, slack_handler)


def register_signal_handlers(slack_handler: SocketModeHandler) -> None:
    """
    Register signal handlers for graceful shutdown.

    Args:
        slack_handler (SocketModeHandler): The active SocketModeHandler instance to shut down.

    Returns:
        None
    """
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, make_signal_handler(slack_handler))


if __name__ == "__main__":  # pragma: no cover
    main(os.environ["SLACK_BOT_TOKEN"], os.environ["SLACK_APP_TOKEN"])
