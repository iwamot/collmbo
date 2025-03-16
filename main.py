import logging
import os
import signal
import sys

from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.bolt_app import create_bolt_app
from app.env import SLACK_APP_LOG_LEVEL


def signal_handler(signum, frame):
    logging.basicConfig(level=SLACK_APP_LOG_LEVEL)
    logger = logging.getLogger(__name__)
    signal_name = signal.Signals(signum).name
    logger.info(f"Received {signal_name}, shutting down...")
    if "handler" in globals():
        try:
            handler.close()
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logging.basicConfig(level=SLACK_APP_LOG_LEVEL)

    app = create_bolt_app(os.environ["SLACK_BOT_TOKEN"])

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
