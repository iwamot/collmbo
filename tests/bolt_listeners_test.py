import pytest

from app.bolt_listeners import (
    build_system_text,
    format_litellm_message_content,
    redact_string,
)


@pytest.mark.parametrize(
    "content, expected",
    [
        (
            """#include &lt;stdio.h&gt;
int main(int argc, char *argv[])
{
    printf("Hello, world!\n");
    return 0;
}""",
            """#include <stdio.h>
int main(int argc, char *argv[])
{
    printf("Hello, world!\n");
    return 0;
}""",
        ),
    ],
)
def test_format_litellm_message_content(content, expected):
    result = format_litellm_message_content(content)
    assert result == expected


def test_build_system_text():
    template = "Hello, {bot_user_id}!"
    bot_user_id = "U12345678"
    expected_output = "Hello, U12345678!"

    result = build_system_text(template, bot_user_id)
    assert result == expected_output


@pytest.mark.parametrize(
    "input_string, patterns, expected_output",
    [
        (
            "My email is test@example.com and my phone is 123-456-7890",
            [
                ("test@example\\.com", "[EMAIL]"),
                ("123-456-7890", "[PHONE]"),
            ],
            "My email is [EMAIL] and my phone is [PHONE]",
        ),
        (
            "No sensitive data here",
            [("test@example\\.com", "[EMAIL]")],
            "No sensitive data here",
        ),
    ],
)
def test_redact_string(input_string, patterns, expected_output):
    assert redact_string(input_string, patterns) == expected_output
