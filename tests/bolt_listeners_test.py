from unittest.mock import MagicMock, patch

import pytest
from slack_bolt import BoltContext
from slack_sdk.web import WebClient

from app.bolt_listeners import (
    can_bot_read_files,
    find_parent_message,
    format_litellm_message_content,
    initialize_messages,
    is_in_thread_started_by_app_mention,
    is_this_app_mentioned,
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
    "bot_user_id, text, expected",
    [
        ("U12345", "Hello <@U12345>", True),
        ("U12345", "No mention here", False),
        (None, "Hello <@U12345>", False),
    ],
)
def test_is_this_app_mentioned(bot_user_id, text, expected):
    assert is_this_app_mentioned(bot_user_id, text) == expected


@patch("app.bolt_listeners.find_parent_message", return_value=None)
@patch("app.bolt_listeners.is_this_app_mentioned")
def test_is_in_thread_started_by_app_mention_no_channel_id(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    mock_context.channel_id = None
    assert (
        is_in_thread_started_by_app_mention(mock_client, mock_context, "12345") is False
    )
    mock_find_parent.assert_not_called()
    mock_is_mentioned.assert_not_called()


@patch("app.bolt_listeners.find_parent_message", return_value=None)
@patch("app.bolt_listeners.is_this_app_mentioned")
def test_is_in_thread_started_by_app_mention_no_thread_ts(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert is_in_thread_started_by_app_mention(mock_client, mock_context, None) is False
    mock_find_parent.assert_not_called()
    mock_is_mentioned.assert_not_called()


@patch("app.bolt_listeners.find_parent_message", return_value=None)
@patch("app.bolt_listeners.is_this_app_mentioned")
def test_is_in_thread_started_by_app_mention_no_parent_message(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert (
        is_in_thread_started_by_app_mention(mock_client, mock_context, "12345") is False
    )
    mock_find_parent.assert_called_once_with(
        mock_client, mock_context.channel_id, "12345"
    )
    mock_is_mentioned.assert_not_called()


@patch("app.bolt_listeners.find_parent_message", return_value={"text": "Hello"})
@patch("app.bolt_listeners.is_this_app_mentioned", return_value=False)
def test_is_in_thread_started_by_app_mention_not_mentioned(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert (
        is_in_thread_started_by_app_mention(mock_client, mock_context, "12345") is False
    )
    mock_find_parent.assert_called_once_with(
        mock_client, mock_context.channel_id, "12345"
    )
    mock_is_mentioned.assert_called_once_with(mock_context.bot_user_id, "Hello")


@patch(
    "app.bolt_listeners.find_parent_message",
    return_value={"text": "Hello <@U87654321>"},
)
@patch("app.bolt_listeners.is_this_app_mentioned", return_value=True)
def test_is_in_thread_started_by_app_mention_true(
    mock_is_mentioned, mock_find_parent, mock_client, mock_context
):
    assert (
        is_in_thread_started_by_app_mention(mock_client, mock_context, "12345") is True
    )
    mock_find_parent.assert_called_once_with(
        mock_client, mock_context.channel_id, "12345"
    )
    mock_is_mentioned.assert_called_once_with(
        mock_context.bot_user_id, "Hello <@U87654321>"
    )


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
def test_initialize_messages(
    template, bot_user_id, translate_markdown, expected_content
):
    result = initialize_messages(template, bot_user_id, translate_markdown)
    assert result == [{"role": "system", "content": expected_content}]


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
