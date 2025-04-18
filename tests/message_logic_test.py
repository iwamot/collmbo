import pytest

from app.message_logic import set_cache_points_if_needed


@pytest.mark.parametrize(
    "prompt_cache_enabled, total_tokens, input_messages, expected_messages",
    [
        (
            False,
            2000,
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {"role": "user", "content": [{"type": "text", "text": "b"}]},
                {"role": "user", "content": [{"type": "text", "text": "c"}]},
            ],
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {"role": "user", "content": [{"type": "text", "text": "b"}]},
                {"role": "user", "content": [{"type": "text", "text": "c"}]},
            ],
        ),
        (
            True,
            500,
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {"role": "user", "content": [{"type": "text", "text": "b"}]},
                {"role": "user", "content": [{"type": "text", "text": "c"}]},
            ],
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {"role": "user", "content": [{"type": "text", "text": "b"}]},
                {"role": "user", "content": [{"type": "text", "text": "c"}]},
            ],
        ),
        (
            True,
            2000,
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
            ],
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
            ],
        ),
        (
            True,
            2000,
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {"role": "user", "content": [{"type": "text", "text": "b"}]},
            ],
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "a",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "b",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
            ],
        ),
        (
            True,
            2000,
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {"role": "user", "content": [{"type": "text", "text": "b"}]},
                {"role": "user", "content": [{"type": "text", "text": "c"}]},
            ],
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "b",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "c",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
            ],
        ),
        (
            True,
            2000,
            [
                {"role": "assistant", "content": "hi"},
                {"role": "user", "content": [{"type": "text", "text": "x"}]},
                {"role": "user", "content": [{"type": "text", "text": "y"}]},
            ],
            [
                {"role": "assistant", "content": "hi"},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "x",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "y",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
            ],
        ),
        (
            True,
            2000,
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {"role": "assistant", "content": "ignored"},
                {"role": "user", "content": [{"type": "text", "text": "b"}]},
                {"role": "user", "content": [{"type": "text", "text": "c"}]},
            ],
            [
                {"role": "user", "content": [{"type": "text", "text": "a"}]},
                {"role": "assistant", "content": "ignored"},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "b",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "c",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                },
            ],
        ),
    ],
)
def test_set_cache_points_if_needed(
    prompt_cache_enabled, total_tokens, input_messages, expected_messages
):
    set_cache_points_if_needed(input_messages, total_tokens, prompt_cache_enabled)

    assert input_messages == expected_messages
