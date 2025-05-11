import pytest

from app.exceptions import ContextOverflowError


@pytest.mark.parametrize(
    "estimated_tokens, max_context_tokens, expected_message",
    [
        (2048, 1024, "The input is too long to be processed (2048/1024 tokens)."),
        (512, 256, "The input is too long to be processed (512/256 tokens)."),
        (100, 100, "The input is too long to be processed (100/100 tokens)."),
    ],
)
def test_context_overflow_error(estimated_tokens, max_context_tokens, expected_message):
    error = ContextOverflowError(estimated_tokens, max_context_tokens)

    assert (
        vars(error)
        == {
            "estimated_tokens": estimated_tokens,
            "max_context_tokens": max_context_tokens,
            "message": expected_message,
        }
        and str(error) == expected_message
    )
