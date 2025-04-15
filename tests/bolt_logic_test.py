import pytest
from slack_bolt import BoltContext
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from app.bolt_logic import (
    append_rate_limit_retry_handler,
    determine_thread_ts_to_reply,
    extract_user_id_from_context,
    is_post_from_bot,
    is_post_in_dm,
    is_post_mentioned,
    should_skip_event,
)


def test_append_rate_limit_retry_handler():
    handlers = []

    append_rate_limit_retry_handler(handlers, 3)

    assert len(handlers) == 1
    assert isinstance(handlers[0], RateLimitErrorRetryHandler)
    assert handlers[0].max_retry_count == 3


@pytest.mark.parametrize(
    "body, payload, expected",
    [
        (
            {"type": "event_callback", "event": {"type": "message"}},
            {"type": "message", "subtype": "message_changed"},
            True,
        ),
        (
            {"type": "event_callback", "event": {"type": "message"}},
            {"type": "message", "subtype": "message_deleted"},
            True,
        ),
        (
            {"type": "event_callback", "event": {"type": "message"}},
            {"type": "message", "subtype": "message_replied"},
            False,
        ),
        (
            {"type": "event_callback", "event": {"type": "reaction_added"}},
            {"type": "reaction_added", "subtype": "message_changed"},
            False,
        ),
        (
            {"type": "event_callback", "event": {}},
            {"type": "message", "subtype": "message_changed"},
            False,
        ),
        (
            {"type": "event_callback"},
            {"type": "message", "subtype": "message_changed"},
            False,
        ),
        (
            {"type": "block_actions", "event": {"type": "message"}},
            {"type": "message", "subtype": "message_changed"},
            False,
        ),
        (
            None,
            {"type": "message", "subtype": "message_changed"},
            False,
        ),
    ],
)
def test_should_skip_event(body, payload, expected):
    result = should_skip_event(body, payload)

    assert result == expected


@pytest.mark.parametrize(
    "actor_user_id, user_id, expected",
    [
        ("U_ACTOR", "U_USER", "U_ACTOR"),
        (None, "U_USER", "U_USER"),
        (None, None, None),
    ],
)
def test_extract_user_id_from_context(actor_user_id, user_id, expected):
    context = BoltContext(actor_user_id=actor_user_id, user_id=user_id)

    result = extract_user_id_from_context(context)

    assert result == expected


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"bot_id": "B123456"}, True),
        ({"bot_id": ""}, True),
        ({"bot_id": None}, False),
        ({}, False),
    ],
)
def test_is_post_from_bot(payload, expected):
    result = is_post_from_bot(payload)

    assert result == expected


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"channel_type": "im"}, True),
        ({"channel_type": "channel"}, False),
        ({"channel_type": None}, False),
        ({}, False),
    ],
)
def test_is_post_in_dm(payload, expected):
    result = is_post_in_dm(payload)

    assert result == expected


@pytest.mark.parametrize(
    "bot_user_id, post, expected",
    [
        ("U12345", {"text": "Hello <@U12345>"}, True),
        ("U12345", {"text": "No mention here"}, False),
        ("U12345", {"text": ""}, False),
        ("U12345", {}, False),
        ("U12345", None, False),
        (None, {"text": "Hello <@U12345>"}, False),
    ],
)
def test_is_post_mentioned(bot_user_id, post, expected):
    result = is_post_mentioned(bot_user_id, post)

    assert result == expected


@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            {"thread_ts": "123.456", "ts": "999.999", "channel_type": "channel"},
            "123.456",
        ),
        ({"ts": "789.789", "channel_type": "channel"}, "789.789"),
        (
            {"thread_ts": "123.456", "ts": "999.999", "channel_type": "im"},
            "123.456",
        ),
        ({"ts": "789.789", "channel_type": "im"}, None),
    ],
)
def test_determine_thread_ts_to_reply(payload, expected):
    result = determine_thread_ts_to_reply(payload)

    assert result == expected
