"""
This module contains middleware functions for the Slack Bolt app.
"""

import logging
from typing import Callable, Optional

from slack_bolt import BoltContext, BoltResponse
from slack_bolt.request.payload_utils import is_event
from slack_sdk.web import WebClient


def before_authorize(
    body: dict,
    payload: dict,
    logger: logging.Logger,
    next_: Callable[[], None],
) -> Optional[BoltResponse]:
    """
    Skip message changed/deleted events to reduce unnecessary workload.

    Especially, "message_changed" events can be triggered many times when the app rapidly updates
    its reply.

    Args:
        body (dict): The request body.
        payload (dict): The request payload.
        logger (logging.Logger): The logger instance.
        next_ (Callable[[], None]): The next middleware function to call.
    Returns:
        Optional[BoltResponse]: A BoltResponse object if the event is skipped, None otherwise.
    """
    if (
        is_event(body)
        and payload.get("type") == "message"
        and payload.get("subtype") in ["message_changed", "message_deleted"]
    ):
        logger.debug(
            "Skipped the following middleware and listeners "
            f"for this message event (subtype: {payload.get('subtype')})"
        )
        return BoltResponse(status=200, body="")
    next_()
    return None


def set_locale(
    context: BoltContext,
    client: WebClient,
    next_: Callable[[], None],
) -> None:
    """
    Set the locale for the user based on their Slack profile.

    Args:
        context (BoltContext): The Bolt context object.
        client (WebClient): The Slack WebClient instance.
        next_ (Callable[[], None]): The next middleware function to call.
    Returns:
        None
    """
    if user_id := context.actor_user_id or context.user_id:
        user_info = client.users_info(user=user_id, include_locale=True)
        user: dict = user_info.get("user", {})
        context["locale"] = user.get("locale")
    else:
        context["locale"] = None
    next_()
