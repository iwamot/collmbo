import pytest

from app.slack_utils import is_post_this_app_mentioned


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
def test_is_post_this_app_mentioned(bot_user_id, post, expected):
    result = is_post_this_app_mentioned(bot_user_id, post)

    assert result == expected
