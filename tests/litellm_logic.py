import pytest

from app.litellm_logic import get_max_input_tokens


@pytest.mark.parametrize(
    "model_type, expected",
    [
        ("gpt-4", 8192),  # has max_input_tokens and max_tokens
        ("luminous-base", 2048),  # has max_tokens only
        ("assemblyai/nano", None),  # no max_input_tokens or max_tokens
    ],
)
def test_get_max_input_tokens(model_type, expected):
    result = get_max_input_tokens(model_type)

    assert result == expected
