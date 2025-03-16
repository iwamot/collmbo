import logging
import os

from slack_bolt import Ack, App, BoltResponse
from slack_bolt.request.payload_utils import is_event
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from app.bolt_listeners import respond_to_app_mention, respond_to_new_message
from app.bolt_middlewares import set_locale
from app.env import USE_SLACK_LANGUAGE


def just_ack(ack: Ack):
    ack()


def register_listeners(app: App):

    # Chat with the bot
    app.event("app_mention")(ack=just_ack, lazy=[respond_to_app_mention])
    app.event("message")(ack=just_ack, lazy=[respond_to_new_message])


MESSAGE_SUBTYPES_TO_SKIP = ["message_changed", "message_deleted"]


# To reduce unnecessary workload in this app,
# this before_authorize function skips message changed/deleted events.
# Especially, "message_changed" events can be triggered many times when the app rapidly updates its reply.
def before_authorize(
    body: dict,
    payload: dict,
    logger: logging.Logger,
    next_,
):
    if (
        is_event(body)
        and payload.get("type") == "message"
        and payload.get("subtype") in MESSAGE_SUBTYPES_TO_SKIP
    ):
        logger.debug(
            "Skipped the following middleware and listeners "
            f"for this message event (subtype: {payload.get('subtype')})"
        )
        return BoltResponse(status=200, body="")
    next_()


def create_bolt_app() -> App:
    app = App(
        token=os.environ["SLACK_BOT_TOKEN"],
        before_authorize=before_authorize,
        process_before_response=True,
    )
    app.client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=2))

    register_listeners(app)

    if USE_SLACK_LANGUAGE:
        app.middleware(set_locale)

    return app
