import logging
import os
import signal
import sys

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from app.bolt_listeners import before_authorize, register_listeners
from app.bolt_middlewares import set_locale
from app.env import SLACK_APP_LOG_LEVEL, USE_SLACK_LANGUAGE


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

    app = App(
        token=os.environ["SLACK_BOT_TOKEN"],
        before_authorize=before_authorize,
        process_before_response=True,
    )
    app.client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=2))

    register_listeners(app)

    if USE_SLACK_LANGUAGE is True:
        app.middleware(set_locale)

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
