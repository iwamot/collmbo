import logging
import os
import signal
import sys
from types import FrameType
from typing import Optional, Type

from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.bolt_app import create_bolt_app
from app.env import SLACK_APP_LOG_LEVEL


def signal_handler(
    signum: int, _: Optional[FrameType], slack_handler: SocketModeHandler
) -> None:
    logger = logging.getLogger(__name__)
    signal_name = signal.Signals(signum).name
    logger.info("Received %s, shutting down...", signal_name)
    try:
        slack_handler.close()
    except Exception:
        pass
    sys.exit(0)


def main(
    slack_bot_token: str,
    slack_app_token: str,
    slack_handler_cls: Type[SocketModeHandler] = SocketModeHandler,
) -> None:
    logging.basicConfig(level=SLACK_APP_LOG_LEVEL)

    app = create_bolt_app(slack_bot_token)
    slack_handler = slack_handler_cls(app, slack_app_token)

    signal.signal(
        signal.SIGTERM,
        lambda signum, frame: signal_handler(signum, frame, slack_handler),
    )
    signal.signal(
        signal.SIGINT,
        lambda signum, frame: signal_handler(signum, frame, slack_handler),
    )

    slack_handler.start()


if __name__ == "__main__":  # pragma: no cover
    main(os.environ["SLACK_BOT_TOKEN"], os.environ["SLACK_APP_TOKEN"])
