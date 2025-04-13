import pytest

from app.bolt_middlewares import should_skip_event


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
