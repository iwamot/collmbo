import base64
from copy import deepcopy
from itertools import product

import pytest

from app.message_logic import (
    build_assistant_message,
    build_image_url_item,
    build_pdf_file_item,
    build_reply_from_post,
    build_reply_text,
    build_slack_user_prefixed_text,
    build_system_message,
    build_tool_message,
    build_user_message,
    convert_markdown_to_mrkdwn,
    filter_replies_after_last_marker,
    format_assistant_reply_for_slack,
    is_reply_from_bot,
    maybe_redact_string,
    maybe_set_cache_points,
    remove_bot_mention,
)


@pytest.mark.parametrize(
    "reply,bot_user_id,expected",
    [
        ({"user": "U123", "text": "Hello"}, "U123", True),
        ({"user": "U456", "text": "Hello"}, "U123", False),
        # bot_message subtype (incoming webhook / classic bot): no "user" key
        (
            {
                "subtype": "bot_message",
                "username": "Deploy Bot",
                "bot_id": "B123",
                "text": "Hello",
            },
            "U123",
            False,
        ),
    ],
)
def test_is_reply_from_bot(reply, bot_user_id, expected):
    result = is_reply_from_bot(reply, bot_user_id)

    assert result == expected


def test_history_keeps_exactly_the_suffix_after_the_last_bot_marker():
    for marker in ("marker", "RESET [a].* = 日本語"):
        kinds = (
            ({"user": "U456", "text": "hello"}, False),
            ({"user": "U123", "text": "world"}, False),
            ({"user": "U123", "text": f"prefix {marker} suffix"}, True),
            ({"user": "U456", "text": marker}, False),
            ({"user": "U123", "text": ""}, False),
            ({"user": "U123"}, False),
        )
        for size in range(5):
            for selected in product(kinds, repeat=size):
                replies = [
                    deepcopy(reply) | {"ts": str(i)}
                    for i, (reply, _) in enumerate(selected)
                ]
                before = deepcopy(replies)
                cut = max(
                    (i + 1 for i, (_, boundary) in enumerate(selected) if boundary),
                    default=0,
                )
                assert (
                    filter_replies_after_last_marker(
                        replies=replies, bot_user_id="U123", marker_text=marker
                    )
                    == replies[cut:]
                )
                assert replies == before


def test_cache_points_change_only_the_last_blocks_of_the_last_two_user_turns():
    for size in range(6):
        for roles in product(("user", "assistant", "system"), repeat=size):
            users = [i for i, role in enumerate(roles) if role == "user"]
            for enabled, ttl, width in product(
                (False, True), (None, "5m", "1h"), (1, 2)
            ):
                messages: list[dict] = [
                    {
                        "role": role,
                        "content": "hi"
                        if role == "assistant"
                        else [
                            {"type": "text", "text": f"turn {i} block {j} 日本語"}
                            for j in range(width)
                        ],
                    }
                    for i, role in enumerate(roles)
                ]
                expected = deepcopy(messages)
                if enabled and len(users) >= 2:
                    control = {"type": "ephemeral"} | (
                        {} if ttl is None else {"ttl": ttl}
                    )
                    for i in users[-2:]:
                        expected[i]["content"][-1]["cache_control"] = control
                maybe_set_cache_points(messages, enabled, ttl)
                assert messages == expected, (roles, enabled, ttl, width)


@pytest.mark.parametrize(
    "template, bot_user_id, slack_formatting_enabled, prompt_caching_enabled, prompt_caching_ttl, expected",
    [
        (
            "Hello, {bot_user_id}",
            "U12345",
            False,
            False,
            None,
            {"role": "system", "content": [{"type": "text", "text": "Hello, U12345"}]},
        ),
        (
            "*Hello*, {bot_user_id}!",
            "U12345",
            True,
            False,
            None,
            {
                "role": "system",
                "content": [{"type": "text", "text": "**Hello**, U12345!"}],
            },
        ),
        (
            "_Welcome_ <@{bot_user_id}> to the channel.",
            "U67890",
            True,
            True,
            None,
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "*Welcome* <@U67890> to the channel.",
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            },
        ),
        (
            "Your ID is {bot_user_id}",
            None,
            False,
            True,
            None,
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "Your ID is None",
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            },
        ),
        (
            "~bye~ {bot_user_id}",
            "U00000",
            True,
            False,
            None,
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "~~bye~~ U00000",
                    }
                ],
            },
        ),
        (
            "Hello, {bot_user_id}",
            "U12345",
            False,
            True,
            "1h",
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello, U12345",
                        "cache_control": {"type": "ephemeral", "ttl": "1h"},
                    }
                ],
            },
        ),
    ],
)
def test_build_system_message(
    template,
    bot_user_id,
    slack_formatting_enabled,
    prompt_caching_enabled,
    prompt_caching_ttl,
    expected,
):
    result = build_system_message(
        template,
        bot_user_id,
        slack_formatting_enabled,
        prompt_caching_enabled,
        prompt_caching_ttl,
    )

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
    "mime_type, image_bytes, expected",
    [
        (
            "image/png",
            b"\x89PNG\r\n\x1a\n...",
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64,"
                    + base64.b64encode(b"\x89PNG\r\n\x1a\n...").decode()
                },
            },
        ),
        (
            "image/gif",
            b"GIF89a",
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/gif;base64,{base64.b64encode(b'GIF89a').decode()}"
                },
            },
        ),
    ],
)
def test_build_image_url_item(mime_type, image_bytes, expected):
    result = build_image_url_item(mime_type, image_bytes)

    assert result == expected


@pytest.mark.parametrize(
    "filename, pdf_bytes, expected",
    [
        (
            "document.pdf",
            b"%PDF-1.4 content",
            {
                "type": "file",
                "file": {
                    "filename": "document.pdf",
                    "file_data": f"data:application/pdf;base64,{base64.b64encode(b'%PDF-1.4 content').decode()}",
                },
            },
        ),
        (
            None,
            b"%PDF-1.7 content",
            {
                "type": "file",
                "file": {
                    "filename": "unnamed.pdf",
                    "file_data": f"data:application/pdf;base64,{base64.b64encode(b'%PDF-1.7 content').decode()}",
                },
            },
        ),
    ],
)
def test_build_pdf_file_item(filename, pdf_bytes, expected):
    result = build_pdf_file_item(filename, pdf_bytes)

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
    result = maybe_redact_string(
        input_string=input_string,
        patterns=patterns,
        redaction_enabled=redaction_enabled,
    )

    assert result == expected_output


def test_a_post_forwarding_a_message_is_read_with_what_it_forwards():
    # A forwarded message is an attachment holding the original's blocks;
    # the post's text says only what the forwarder wrote.
    payload = {
        "text": "<@UBOT> list the headings",
        "blocks": [
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {"type": "user", "user_id": "UBOT"},
                            {"type": "text", "text": " list the headings"},
                        ],
                    }
                ],
            }
        ],
        "attachments": [
            {
                "is_share": True,
                "is_msg_unfurl": True,
                "text": "Plan",
                "blocks": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_header",
                                "level": 2,
                                "elements": [{"type": "text", "text": "Plan"}],
                            }
                        ],
                    }
                ],
                "from_url": "https://example.slack.com/archives/C1/p1",
            }
        ],
    }
    reply = build_reply_from_post(payload, "U123")

    assert build_reply_text(
        reply, "UBOT", redact_patterns=[], redaction_enabled=False
    ) == (
        "<@U123>: list the headings\n\n## Plan\n\n"
        "https://example.slack.com/archives/C1/p1"
    )


def test_build_reply_text_reads_the_blocks_then_removes_and_redacts():
    # A representative message: the bot's mention, a heading and a list in
    # the blocks, and an address that only the blocks hold in full.
    reply = {
        "user": "U123",
        "text": "<@UBOT> Plan ...",
        "blocks": [
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {"type": "user", "user_id": "UBOT"},
                            {"type": "text", "text": " see the plan\n"},
                        ],
                    },
                    {
                        "type": "rich_text_header",
                        "level": 2,
                        "elements": [{"type": "text", "text": "Plan"}],
                    },
                    {
                        "type": "rich_text_list",
                        "style": "bullet",
                        "indent": 0,
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {"type": "text", "text": "mail "},
                                    {
                                        "type": "text",
                                        "text": "a@example.com",
                                        "style": {"bold": True},
                                    },
                                ],
                            }
                        ],
                    },
                ],
            }
        ],
    }
    patterns = [(r"\b[\w.]+@[\w.]+\b", "[EMAIL]")]

    assert (
        build_reply_text(
            reply, "UBOT", redact_patterns=patterns, redaction_enabled=True
        )
        == "<@U123>: see the plan\n## Plan\n- mail **[EMAIL]**"
    )
    assert (
        build_reply_text(
            reply, "UBOT", redact_patterns=patterns, redaction_enabled=False
        )
        == "<@U123>: see the plan\n## Plan\n- mail **a@example.com**"
    )


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
        ("這是**粗體**文字。", "這是 *粗體* 文字。"),
        ("中文_斜體_中文", "中文 _斜體_ 中文"),
        ("中文~~刪除~~中文，標點", "中文 ~刪除~ 中文，標點"),
        ("括號：「**強調**」", "括號：「 *強調* 」"),
        ("ひらがな**強調**ひらがな", "ひらがな *強調* ひらがな"),
        ("한글**강조**한글", "한글 *강조* 한글"),
        ("ㄅㄆㄇ**強調**ㄈㄉㄊ", "ㄅㄆㄇ *強調* ㄈㄉㄊ"),
        ("ｶﾀｶﾅ**強調**ｶﾀｶﾅ", "ｶﾀｶﾅ*強調*ｶﾀｶﾅ"),
        ("Inline code `**粗體**` test", "Inline code `**粗體**` test"),
        ("中文`程式`中文", "中文 `程式` 中文"),
        ("中文```程式```中文", "中文 ```程式``` 中文"),
        ("括號：「`程式`」", "括號：「 `程式` 」"),
        ("```", "```"),
        ("**文字**", "*文字*"),
        ("文字**強調**", "文字 *強調*"),
    ],
)
def test_convert_markdown_to_mrkdwn(content, expected):
    result = convert_markdown_to_mrkdwn(content)

    assert result == expected


def test_mrkdwn_spaces_formatting_and_code_only_next_to_wide_characters():
    # Slack does not render formatting that touches a wide or fullwidth
    # character, so a space goes between them, and nowhere else.
    wide = {"日", "Ａ", "，", "「"}
    neighbors = ("", " ", "a", "1", ".", "ｶ", *sorted(wide))
    tokens = {
        "`code`": "`code`",
        "```block```": "```block```",
        "**b**": "*b*",
        "_i_": "_i_",
        "~~s~~": "~s~",
    }
    for before, (token, converted), after in product(
        neighbors, tokens.items(), neighbors
    ):
        expected = (
            before
            + (" " if before in wide else "")
            + converted
            + (" " if after in wide else "")
            + after
        )
        assert convert_markdown_to_mrkdwn(before + token + after) == expected, (
            before,
            token,
            after,
        )
