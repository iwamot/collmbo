import logging
from typing import Callable

from slack_bolt import BoltContext, BoltResponse
from slack_bolt.request.payload_utils import is_event
from slack_sdk.web import WebClient

MESSAGE_SUBTYPES_TO_SKIP = ["message_changed", "message_deleted"]


# To reduce unnecessary workload in this app,
# this before_authorize function skips message changed/deleted events.
# Especially, "message_changed" events can be triggered many times when the app rapidly updates its reply.
def before_authorize(
    body: dict,
    payload: dict,
    logger: logging.Logger,
    next_: Callable[[], None],
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


def set_locale(
    context: BoltContext,
    client: WebClient,
    next_: Callable[[], None],
):
    if user_id := context.actor_user_id or context.user_id:
        user_info = client.users_info(user=user_id, include_locale=True)
        user: dict = user_info.get("user", {})
        context["locale"] = user.get("locale")
    else:
        context["locale"] = None
    next_()
