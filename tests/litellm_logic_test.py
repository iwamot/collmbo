import pytest
from litellm.types.utils import Delta, ModelResponse, StreamingChoices

from app.litellm_logic import extract_delta_content, is_final_chunk


@pytest.mark.parametrize(
    "chunk, expected",
    [
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(content="Hello"))],
                object="chat.completion.chunk",
            ),
            "Hello",
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(tool_calls=[]))],
                object="chat.completion.chunk",
            ),
            None,
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=None)],
                object="chat.completion.chunk",
            ),
            None,
        ),
        (
            ModelResponse(
                choices=[],
                object="chat.completion.chunk",
            ),
            None,
        ),
    ],
)
def test_extract_delta_content(chunk, expected):
    result = extract_delta_content(chunk)

    assert result == expected


@pytest.mark.parametrize(
    "chunk, expected",
    [
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(content="Hello"))],
                object="chat.completion.chunk",
            ),
            False,
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(), finish_reason="stop")],
                object="chat.completion.chunk",
            ),
            True,
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=None, finish_reason="length")],
                object="chat.completion.chunk",
            ),
            True,
        ),
    ],
)
def test_is_final_chunk(chunk, expected):
    result = is_final_chunk(chunk)

    assert result == expected
