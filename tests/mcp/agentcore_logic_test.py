import pytest

from app.mcp.agentcore_logic import (
    create_agentcore_user_id,
)


@pytest.mark.parametrize(
    "slack_user_id, session_id, expected",
    [
        (
            "user123",
            "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
            "user123_a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
        ),
        (
            "",
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "_0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        ),
        ("user", "", "user_"),
        ("", "", "_"),
        (
            "test_user",
            "deadbeefcafe1234567890abcdef1234567890abcdef1234567890abcdef1234",
            "test_user_deadbeefcafe1234567890abcdef1234567890abcdef1234567890abcdef1234",
        ),
        (
            "U12345678",
            "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
            "U12345678_f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
        ),
    ],
)
def test_create_agentcore_user_id(slack_user_id, session_id, expected):
    result = create_agentcore_user_id(slack_user_id, session_id)

    assert result == expected
