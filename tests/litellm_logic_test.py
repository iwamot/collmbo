import pytest
from litellm.types.utils import Choices, Delta, Message, ModelResponse, StreamingChoices

from app.litellm_logic import (
    extract_delta_content,
    has_visible_text,
    is_final_chunk,
)


@pytest.mark.parametrize(
    "chunk, expected",
    [
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(content="Hello"))],
                stream=True,
            ),
            "Hello",
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(tool_calls=[]))],
                stream=True,
            ),
            None,
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=None)],
                stream=True,
            ),
            None,
        ),
        (
            ModelResponse(
                choices=[],
                stream=True,
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
                choices=[
                    Choices(
                        finish_reason="stop",
                        index=0,
                        message=Message(content="Hello"),
                    )
                ],
            ),
            True,
        ),
        (
            ModelResponse(
                choices=[
                    Choices(
                        finish_reason="length",
                        index=0,
                        message=Message(role="assistant"),
                    )
                ],
            ),
            True,
        ),
    ],
)
def test_is_final_chunk(chunk, expected):
    result = is_final_chunk(chunk)

    assert result == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        # Real narration -> visible text, must be preserved
        ("Let me check the weather for you.", True),
        # Pure tool call leaves content empty -> nothing to preserve
        ("", False),
        # Reasoning models can emit whitespace-only content on a tool-call turn
        ("   \n\t ", False),
    ],
)
def test_has_visible_text(content, expected):
    result = has_visible_text(content)

    assert result == expected
