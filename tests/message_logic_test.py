import pytest

from app.message_logic import (
    build_assistant_message,
    build_slack_user_prefixed_text,
    build_system_message,
    build_tool_message,
    build_user_message,
    convert_markdown_to_mrkdwn,
    format_assistant_reply_for_slack,
    maybe_redact_string,
    maybe_set_cache_points,
    maybe_slack_to_markdown,
    remove_bot_mention,
    unescape_slack_formatting,
)


@pytest.mark.parametrize(
    "template, bot_user_id, translate_markdown, expected",
    [
        (
            "Hello, {bot_user_id}",
            "U12345",
            False,
            {"role": "system", "content": "Hello, U12345"},
        ),
        (
            "*Hello*, {bot_user_id}!",
            "U12345",
            True,
            {"role": "system", "content": "**Hello**, U12345!"},
        ),
        (
            "_Welcome_ <@{bot_user_id}> to the channel.",
            "U67890",
            True,
            {"role": "system", "content": "*Welcome* <@U67890> to the channel."},
        ),
        (
            "Your ID is {bot_user_id}",
            None,
            False,
            {"role": "system", "content": "Your ID is None"},
        ),
        (
            "~~bye~~ {bot_user_id}",
            "U00000",
            True,
            {"role": "system", "content": "~~~bye~~~ U00000"},
        ),
    ],
)
def test_build_system_message(template, bot_user_id, translate_markdown, expected):
    result = build_system_message(template, bot_user_id, translate_markdown)

    assert result == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello!", {"role": "assistant", "content": "Hello!"}),
        ("", {"role": "assistant", "content": ""}),
    ],
)
def test_build_assistant_message(text, expected):
    result = build_assistant_message(text)

    assert result == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        (
            [{"type": "text", "text": "hello"}],
            {"role": "user", "content": [{"type": "text", "text": "hello"}]},
        ),
        ([], {"role": "user", "content": []}),
    ],
)
def test_build_user_message(content, expected):
    result = build_user_message(content)

    assert result == expected


@pytest.mark.parametrize(
    "tool_call_id, name, content, expected",
    [
        (
            "abc123",
            "get_weather",
            "Sunny",
            {
                "tool_call_id": "abc123",
                "role": "tool",
                "name": "get_weather",
                "content": "Sunny",
            },
        ),
        (
            "xyz789",
            "translate",
            "",
            {
                "tool_call_id": "xyz789",
                "role": "tool",
                "name": "translate",
                "content": "",
            },
        ),
    ],
)
def test_build_tool_message(tool_call_id, name, content, expected):
    result = build_tool_message(tool_call_id=tool_call_id, name=name, content=content)

    assert result == expected


@pytest.mark.parametrize(
    "text, bot_user_id, expected",
    [
        ("<@U12345> hello", "U12345", "hello"),
        ("<@U12345>hello", "U12345", "hello"),
        ("<@U12345>    hello", "U12345", "hello"),
        ("hello", "U12345", "hello"),
        ("<@U67890> hello", "U12345", "<@U67890> hello"),
        ("<@None> hello", None, "<@None> hello"),
    ],
)
def test_remove_bot_mention(text, bot_user_id, expected):
    assert remove_bot_mention(text, bot_user_id) == expected


@pytest.mark.parametrize(
    "input_string, patterns, redaction_enabled, expected_output",
    [
        (
            "My email is test@example.com and my phone is 123-456-7890",
            [("test@example\\.com", "[EMAIL]"), ("123-456-7890", "[PHONE]")],
            True,
            "My email is [EMAIL] and my phone is [PHONE]",
        ),
        (
            "No sensitive data here",
            [("test@example\\.com", "[EMAIL]")],
            True,
            "No sensitive data here",
        ),
        (
            "My email is test@example.com and my phone is 123-456-7890",
            [("test@example\\.com", "[EMAIL]"), ("123-456-7890", "[PHONE]")],
            False,
            "My email is test@example.com and my phone is 123-456-7890",
        ),
        (
            "No sensitive data here",
            [("test@example\\.com", "[EMAIL]")],
            False,
            "No sensitive data here",
        ),
    ],
)
def test_maybe_redact_string(
    input_string, patterns, redaction_enabled, expected_output
):
    result = maybe_redact_string(input_string, patterns, redaction_enabled)

    assert result == expected_output


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
def test_unescape_slack_formatting(content, expected):
    result = unescape_slack_formatting(content)
    assert result == expected


@pytest.mark.parametrize(
    "content, translate_markdown, expected",
    [
        (
            "Sentence with *bold text*, _italic text_ and ~strikethrough text~.",
            True,
            "Sentence with **bold text**, *italic text* and ~~strikethrough text~~.",
        ),
        (
            "Sentence with _*bold and italic text*_ and *_bold and italic text_*.",
            True,
            "Sentence with ***bold and italic text*** and ***bold and italic text***.",
        ),
        (
            "Code block ```*text*, _text_ and ~text~``` shouldn't be changed.",
            True,
            "Code block ```*text*, _text_ and ~text~``` shouldn't be changed.",
        ),
        (
            "Inline code `*text*, _text_ and ~text~` shouldn't be changed.",
            True,
            "Inline code `*text*, _text_ and ~text~` shouldn't be changed.",
        ),
        (
            "```Some `*bold text* inside inline code` inside a code block``` shouldn't be changed.",
            True,
            "```Some `*bold text* inside inline code` inside a code block``` shouldn't be changed.",
        ),
        (
            "* bullets shouldn't\n* be changed",
            True,
            "* bullets shouldn't\n* be changed",
        ),
        (
            "* not bold*, *not bold *, * not bold *, **, * *, *  *, *   *",
            True,
            "* not bold*, *not bold *, * not bold *, **, * *, *  *, *   *",
        ),
        (
            "_ not italic_, _not italic _, _ not italic _, __, _ _, _  _, _   _",
            True,
            "_ not italic_, _not italic _, _ not italic _, __, _ _, _  _, _   _",
        ),
        (
            "~ not strikethrough~, ~not strikethrough ~, ~ not strikethrough ~, ~~, ~ ~, ~  ~, ~   ~",
            True,
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
            True,
            """The following multiline code block shouldn't be translated:
```
if 4*q + r - t < n*t:
    q, r, t, k, n, l = 10*q, 10*(r-n*t), t, k, (10*(3*q+r))//t - 10*n, l
else:
    q, r, t, k, n, l = q*l, (2*q+r)*l, t*l, k+1, (q*(7*k+2)+r*l)//(t*l), l+2
```""",
        ),
        (
            "Sentence with *bold text*, _italic text_ and ~strikethrough text~.",
            False,
            "Sentence with *bold text*, _italic text_ and ~strikethrough text~.",
        ),
        (
            "Sentence with _*bold and italic text*_ and *_bold and italic text_*.",
            False,
            "Sentence with _*bold and italic text*_ and *_bold and italic text_*.",
        ),
        (
            "Code block ```*text*, _text_ and ~text~``` shouldn't be changed.",
            False,
            "Code block ```*text*, _text_ and ~text~``` shouldn't be changed.",
        ),
    ],
)
def test_maybe_slack_to_markdown(content, translate_markdown, expected):
    result = maybe_slack_to_markdown(content, translate_markdown)

    assert result == expected


@pytest.mark.parametrize(
    "reply, text, expected",
    [
        ({"user": "U123"}, "hello", "<@U123>: hello"),
        ({"username": "someone"}, "hi", "<@someone>: hi"),
        ({}, "yo", "<@None>: yo"),
    ],
)
def test_build_slack_user_prefixed_text(reply, text, expected):
    result = build_slack_user_prefixed_text(reply, text)

    assert result == expected


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
                {"role": "user", "content": [{"type": "text", "text": "x"}]},
                {"role": "assistant", "content": "hi"},
                {"role": "user", "content": [{"type": "text", "text": "y"}]},
            ],
            [
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
                {"role": "assistant", "content": "hi"},
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
def test_maybe_set_cache_points(
    prompt_cache_enabled, total_tokens, input_messages, expected_messages
):
    maybe_set_cache_points(input_messages, total_tokens, prompt_cache_enabled)

    assert input_messages == expected_messages


@pytest.mark.parametrize(
    "content, expected",
    [
        (
            "\n\nSorry, I cannot answer the question.",
            "Sorry, I cannot answer the question.",
        ),
        ("\n\n```python\necho 'foo'\n```", "```\necho 'foo'\n```"),
        ("\n\n```ruby\nputs 'foo'\n```", "```\nputs 'foo'\n```"),
        (
            "\n\n```java\nSystem.out.println(123);\n```",
            "```\nSystem.out.println(123);\n```",
        ),
        ("\n\n```C\n#include <stdio.h>\n```", "```\n#include <stdio.h>\n```"),
        ("\n\n```c\n#include <stdio.h>\n```", "```\n#include <stdio.h>\n```"),
        ("\n\n```C++\n#include <iostream>\n```", "```\n#include <iostream>\n```"),
        ("\n\n```c++\n#include <iostream>\n```", "```\n#include <iostream>\n```"),
        ("\n\n```Cpp\n#include <iostream>\n```", "```\n#include <iostream>\n```"),
        ("\n\n```cpp\n#include <iostream>\n```", "```\n#include <iostream>\n```"),
        ("\n\n```Csharp\nusing System;\n```", "```\nusing System;\n```"),
        ("\n\n```csharp\nusing System;\n```", "```\nusing System;\n```"),
        ("\n\n```Matlab\ndisp('foo');\n```", "```\ndisp('foo');\n```"),
        ("\n\n```matlab\ndisp('foo');\n```", "```\ndisp('foo');\n```"),
        ("\n\n```JSON\n{\n```", "```\n{\n```"),
        ("\n\n```json\n{\n```", "```\n{\n```"),
        (
            "\n\n```LaTeX\n\\documentclass{article}\n```",
            "```\n\\documentclass{article}\n```",
        ),
        (
            "\n\n```latex\n\\documentclass{article}\n```",
            "```\n\\documentclass{article}\n```",
        ),
        ("\n\n```lua\nx = 1\n```", "```\nx = 1\n```"),
        (
            "\n\n```cmake\ncmake_minimum_required(VERSION 3.24)\n```",
            "```\ncmake_minimum_required(VERSION 3.24)\n```",
        ),
        ("\n\n```bash\n#!/bin/bash\n```", "```\n#!/bin/bash\n```"),
        ("\n\n```zsh\n#!/bin/zsh\n```", "```\n#!/bin/zsh\n```"),
        ("\n\n```sh\n#!/bin/sh\n```", "```\n#!/bin/sh\n```"),
    ],
)
def test_format_assistant_reply_for_slack(content, expected):
    result = format_assistant_reply_for_slack(content)

    assert result == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        (
            "Sentence with **bold text**, __bold text__, *italic text*, _italic text_ and ~~strikethrough text~~.",
            "Sentence with *bold text*, *bold text*, _italic text_, _italic text_ and ~strikethrough text~.",
        ),
        (
            "Sentence with ***bold and italic text***, **_bold and italic text_**, and _**bold and italic text**_.",
            "Sentence with _*bold and italic text*_, *_bold and italic text_*, and _*bold and italic text*_.",
        ),
        (
            "Code block ```**text**, __text__, *text*, _text_ and ~~text~~``` shouldn't be changed.",
            "Code block ```**text**, __text__, *text*, _text_ and ~~text~~``` shouldn't be changed.",
        ),
        (
            "```Some `**bold text** inside inline code` inside a code block``` shouldn't be changed.",
            "```Some `**bold text** inside inline code` inside a code block``` shouldn't be changed.",
        ),
        (
            "Inline code `**text**, __text__, *text*, _text_ and ~~text~~` shouldn't be changed.",
            "Inline code `**text**, __text__, *text*, _text_ and ~~text~~` shouldn't be changed.",
        ),
        ("* bullets shouldn't\n* be changed", "* bullets shouldn't\n* be changed"),
        (
            "** not bold**, **not bold **, ** not bold **, ****, ** **, **  **, **   **",
            "** not bold**, **not bold **, ** not bold **, ****, ** **, **  **, **   **",
        ),
        (
            "__ not bold__, __not bold __, __ not bold __, ____, __ __, __  __, __   __",
            "__ not bold__, __not bold __, __ not bold __, ____, __ __, __  __, __   __",
        ),
        (
            "* not italic*, *not italic *, * not italic *, **, * *, *  *, *   *",
            "* not italic*, *not italic *, * not italic *, **, * *, *  *, *   *",
        ),
        (
            "_ not italic_, _not italic _, _ not italic _, __, _ _, _  _, _   _",
            "_ not italic_, _not italic _, _ not italic _, __, _ _, _  _, _   _",
        ),
        (
            "~~ not strikethrough~~, ~~not strikethrough ~~, ~~ not strikethrough ~~, ~~~~, ~~ ~~, ~~  ~~, ~~   ~~",
            "~~ not strikethrough~~, ~~not strikethrough ~~, ~~ not strikethrough ~~, ~~~~, ~~ ~~, ~~  ~~, ~~   ~~",
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
def test_convert_markdown_to_mrkdwn(content, expected):
    result = convert_markdown_to_mrkdwn(content)

    assert result == expected
