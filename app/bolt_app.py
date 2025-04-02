from slack_bolt import Ack, App
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from app.bolt_listeners import respond_to_new_message
from app.bolt_middlewares import before_authorize, set_locale
from app.env import USE_SLACK_LANGUAGE


def just_ack(ack: Ack):
    ack()


def create_bolt_app(
    slack_bot_token: str,
    use_slack_language: bool = USE_SLACK_LANGUAGE,
) -> App:
    app = App(
        token=slack_bot_token,
        before_authorize=before_authorize,
        process_before_response=True,
    )
    app.client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=2))

    app.event("message")(ack=just_ack, lazy=[respond_to_new_message])

    if use_slack_language:
        app.middleware(set_locale)

    return app
