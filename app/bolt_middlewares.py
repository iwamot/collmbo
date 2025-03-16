from slack_bolt import BoltContext
from slack_sdk.web import WebClient


def set_locale(
    context: BoltContext,
    client: WebClient,
    next_,
):
    if user_id := context.actor_user_id or context.user_id:
        user_info = client.users_info(user=user_id, include_locale=True)
        user: dict = user_info.get("user", {})
        context["locale"] = user.get("locale")
    else:
        context["locale"] = None
    next_()
