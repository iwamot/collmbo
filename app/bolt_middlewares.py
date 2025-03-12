from slack_bolt import BoltContext
from slack_sdk.web import WebClient

from app.env import IMAGE_FILE_ACCESS_ENABLED, PDF_FILE_ACCESS_ENABLED


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


def attach_bot_scopes(client: WebClient, context: BoltContext, next_):
    if (
        # the bot_scopes is used for #can_send_*_url_to_litellm method calls
        (IMAGE_FILE_ACCESS_ENABLED is True or PDF_FILE_ACCESS_ENABLED is True)
        and context.authorize_result is not None
        and context.authorize_result.bot_scopes is None
    ):
        auth_test = client.auth_test(token=context.bot_token)
        scopes = auth_test.headers.get("x-oauth-scopes", [])
        context.authorize_result.bot_scopes = scopes
    next_()
