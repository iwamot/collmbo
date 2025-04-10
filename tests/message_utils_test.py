from unittest.mock import MagicMock

import pytest
from slack_bolt import BoltContext
from slack_sdk.web import WebClient

from app.message_utils import (
    build_system_message,
    can_bot_read_files,
    format_litellm_message_content,
    maybe_redact_string,
    maybe_slack_to_markdown,
)


@pytest.fixture
def mock_client():
    return MagicMock(spec=WebClient)


@pytest.fixture
def mock_context():
    context = MagicMock(spec=BoltContext)
    context.channel_id = "C12345678"
    context.bot_user_id = "U87654321"
    return context


@pytest.mark.parametrize(
    "template, bot_user_id, translate_markdown, expected_content",
    [
        (
            "Hello, {bot_user_id}!",
            "U12345678",
            False,
            "Hello, U12345678!",
        ),
        (
            "Hello, *{bot_user_id}* and _you_!",
            "U12345678",
            True,
            "Hello, **U12345678** and *you*!",
        ),
    ],
)
def test_build_system_message(
    template, bot_user_id, translate_markdown, expected_content
):
    result = build_system_message(template, bot_user_id, translate_markdown)
    assert result == {"role": "system", "content": expected_content}


@pytest.mark.parametrize(
    "bot_scopes, expected",
    [
        (None, False),
        (["chat:write", "users:read"], False),
        (["files:read", "chat:write"], True),
    ],
)
def test_can_bot_read_files(bot_scopes, expected):
    assert can_bot_read_files(bot_scopes) == expected


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


@pytest.mark.parametrize(
    "content, expected",
    [
        (
            "Sentence with *bold text*, _italic text_ and ~strikethrough text~.",
            "Sentence with **bold text**, *italic text* and ~~strikethrough text~~.",
        ),
        (
            "Sentence with _*bold and italic text*_ and *_bold and italic text_*.",
            "Sentence with ***bold and italic text*** and ***bold and italic text***.",
        ),
        (
            "Code block ```*text*, _text_ and ~text~``` shouldn't be changed.",
            "Code block ```*text*, _text_ and ~text~``` shouldn't be changed.",
        ),
        (
            "Inline code `*text*, _text_ and ~text~` shouldn't be changed.",
            "Inline code `*text*, _text_ and ~text~` shouldn't be changed.",
        ),
        (
            "```Some `*bold text* inside inline code` inside a code block``` shouldn't be changed.",
            "```Some `*bold text* inside inline code` inside a code block``` shouldn't be changed.",
        ),
        ("* bullets shouldn't\n* be changed", "* bullets shouldn't\n* be changed"),
        (
            "* not bold*, *not bold *, * not bold *, **, * *, *  *, *   *",
            "* not bold*, *not bold *, * not bold *, **, * *, *  *, *   *",
        ),
        (
            "_ not italic_, _not italic _, _ not italic _, __, _ _, _  _, _   _",
            "_ not italic_, _not italic _, _ not italic _, __, _ _, _  _, _   _",
        ),
        (
            "~ not strikethrough~, ~not strikethrough ~, ~ not strikethrough ~, ~~, ~ ~, ~  ~, ~   ~",
            "~ not strikethrough~, ~not strikethrough ~, ~ not strikethrough ~, ~~, ~ ~, ~  ~, ~   ~",
        ),
        (
            """The following multiline code block shouldn't be translated:
```
if 4*q + r - t < n*t:
    q, r, t, k, n, l = 10*q, 10*(r-n*t), t, k, (10*(3*q+r))//t - 10*n, l
else:
    q, r, t, k, n, l = q*l, (2*q+r)*l, t*l, k+1, (q*(7*k+2)+r*l)//(t*l), l+2
```""",
            """The following multiline code block shouldn't be translated:
```
if 4*q + r - t < n*t:
    q, r, t, k, n, l = 10*q, 10*(r-n*t), t, k, (10*(3*q+r))//t - 10*n, l
else:
    q, r, t, k, n, l = q*l, (2*q+r)*l, t*l, k+1, (q*(7*k+2)+r*l)//(t*l), l+2
```""",
        ),
    ],
)
def test_maybe_slack_to_markdown_enabled(content, expected):
    result = maybe_slack_to_markdown(content, translate_markdown=True)
    assert result == expected


@pytest.mark.parametrize(
    "content",
    [
        ("Sentence with *bold text*, _italic text_ and ~strikethrough text~.",),
        ("Sentence with _*bold and italic text*_ and *_bold and italic text_*.",),
        ("Code block ```*text*, _text_ and ~text~``` shouldn't be changed.",),
        ("Inline code `*text*, _text_ and ~text~` shouldn't be changed.",),
        (
            "```Some `*bold text* inside inline code` inside a code block``` shouldn't be changed.",
        ),
        ("* bullets shouldn't\n* be changed",),
        ("* not bold*, *not bold *, * not bold *, **, * *, *  *, *   *",),
        ("_ not italic_, _not italic _, _ not italic _, __, _ _, _  _, _   _",),
        (
            "~ not strikethrough~, ~not strikethrough ~, ~ not strikethrough ~, ~~, ~ ~, ~  ~, ~   ~",
        ),
        (
            """The following multiline code block shouldn't be translated:
```
if 4*q + r - t < n*t:
    q, r, t, k, n, l = 10*q, 10*(r-n*t), t, k, (10*(3*q+r))//t - 10*n, l
else:
    q, r, t, k, n, l = q*l, (2*q+r)*l, t*l, k+1, (q*(7*k+2)+r*l)//(t*l), l+2
```""",
        ),
    ],
)
def test_maybe_slack_to_markdown_disabled(content):
    result = maybe_slack_to_markdown(content, translate_markdown=False)
    assert result == content


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
def test_maybe_redact_string_enabled(input_string, patterns, expected_output):
    assert (
        maybe_redact_string(input_string, patterns, redaction_enabled=True)
        == expected_output
    )


@pytest.mark.parametrize(
    "input_string, patterns",
    [
        (
            "My email is test@example.com and my phone is 123-456-7890",
            [
                ("test@example\\.com", "[EMAIL]"),
                ("123-456-7890", "[PHONE]"),
            ],
        ),
        (
            "No sensitive data here",
            [("test@example\\.com", "[EMAIL]")],
        ),
    ],
)
def test_maybe_redact_string_disabled(input_string, patterns):
    assert (
        maybe_redact_string(input_string, patterns, redaction_enabled=False)
        == input_string
    )
