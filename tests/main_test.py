from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from main import append_rate_limit_retry_handler


def test_append_rate_limit_retry_handler():
    handlers = []

    append_rate_limit_retry_handler(handlers, 3)

    assert len(handlers) == 1
    assert isinstance(handlers[0], RateLimitErrorRetryHandler)
    assert handlers[0].max_retry_count == 3
