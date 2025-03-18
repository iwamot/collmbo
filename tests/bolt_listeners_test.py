from unittest.mock import MagicMock

import pytest
from slack_sdk.web import WebClient

from app.bolt_listeners import (
    build_system_text,
    can_bot_read_files,
    find_parent_message,
    format_litellm_message_content,
    is_this_app_mentioned,
    redact_string,
    slack_to_markdown,
)


def test_find_parent_message_with_valid_response():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {
        "messages": [{"text": "Hello, world!"}]
    }

    result = find_parent_message(mock_client, "C12345678", "123456.789")
    assert result == {"text": "Hello, world!"}


def test_find_parent_message_with_no_messages():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {"messages": []}

    result = find_parent_message(mock_client, "C12345678", "123456.789")
    assert result is None


def test_find_parent_message_with_none_channel_id():
    mock_client = MagicMock(spec=WebClient)

    result = find_parent_message(mock_client, None, "123456.789")
    assert result is None


def test_find_parent_message_with_none_thread_ts():
    mock_client = MagicMock(spec=WebClient)

    result = find_parent_message(mock_client, "C12345678", None)
    assert result is None


def test_find_parent_message_with_invalid_response():
    mock_client = MagicMock(spec=WebClient)
    mock_client.conversations_history.return_value = {"not_messages": []}

    result = find_parent_message(mock_client, "C12345678", "123456.789")
    assert result is None


@pytest.mark.parametrize(
    "bot_user_id, parent_message, expected",
    [
        ("U12345", {"text": "Hello <@U12345>"}, True),
        ("U12345", {"text": "No mention here"}, False),
        (None, {"text": "Hello <@U12345>"}, False),
    ],
)
def test_is_this_app_mentioned(bot_user_id, parent_message, expected):
    assert is_this_app_mentioned(bot_user_id, parent_message) == expected


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


def test_build_system_text():
    template = "Hello, {bot_user_id}!"
    bot_user_id = "U12345678"
    expected_output = "Hello, U12345678!"

    result = build_system_text(template, bot_user_id)
    assert result == expected_output


def test_slack_to_markdown():
    for content, expected in [
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
    ]:
        result = slack_to_markdown(content)
        assert result == expected


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
