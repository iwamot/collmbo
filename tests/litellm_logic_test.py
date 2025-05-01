import pytest

from app.litellm_logic import (
    calculate_max_context_tokens,
    get_max_input_tokens,
    load_tools_from_module,
    trim_messages_to_max_context_tokens,
)


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


@pytest.mark.parametrize(
    "max_input_tokens, tools_tokens, max_output_tokens, expected",
    [
        (1000, 100, 200, 700),
        (100, 100, 100, 0),
    ],
)
def test_calculate_max_context_tokens(
    max_input_tokens, tools_tokens, max_output_tokens, expected
):
    result = calculate_max_context_tokens(
        max_input_tokens, tools_tokens, max_output_tokens
    )

    assert result == expected


@pytest.mark.parametrize(
    "messages, max_context_tokens, expected_tokens, expected_len",
    [
        (
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi, how can I help you today?"},
                {"role": "user", "content": "Tell me a joke."},
            ],
            35,
            35,
            3,
        ),
        (
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi, how can I help you today?"},
            ],
            32,
            32,
            3,
        ),
        (
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's the weather like?"},
            ],
            20,
            22,
            2,
        ),
        (
            [
                {"role": "system", "content": "System message 1."},
                {"role": "system", "content": "System message 2."},
                {"role": "system", "content": "System message 3."},
            ],
            10,
            30,
            3,
        ),
    ],
)
def test_trim_messages_to_max_context_tokens(
    messages, max_context_tokens, expected_tokens, expected_len
):
    result = trim_messages_to_max_context_tokens(
        messages=messages,
        model_type="gpt-4o",
        max_context_tokens=max_context_tokens,
    )

    assert result == expected_tokens
    assert len(messages) == expected_len


@pytest.mark.parametrize(
    "module_name, expected_type",
    [
        ("examples.tools", list),
        (None, type(None)),
    ],
)
def test_load_tools_from_module_type(module_name, expected_type):
    result = load_tools_from_module(module_name)

    assert isinstance(result, expected_type)
