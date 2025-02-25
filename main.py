import logging
import os
import signal
import sys

from slack_bolt import App, BoltContext
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
from slack_sdk.web import WebClient

from app.bolt_listeners import before_authorize, register_listeners
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

    from slack_bolt.adapter.socket_mode import SocketModeHandler

    logging.basicConfig(level=SLACK_APP_LOG_LEVEL)

    app = App(
        token=os.environ["SLACK_BOT_TOKEN"],
        before_authorize=before_authorize,
        process_before_response=True,
    )
    app.client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=2))

    register_listeners(app)

    if USE_SLACK_LANGUAGE is True:

        @app.middleware
        def set_locale(
            context: BoltContext,
            client: WebClient,
            next_,
        ):
            user_id = context.actor_user_id or context.user_id
            if user_id:
                user_info = client.users_info(user=user_id, include_locale=True)
                user: dict = user_info.get("user", {})
                context["locale"] = user.get("locale")
            else:
                context["locale"] = None
            next_()

    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
