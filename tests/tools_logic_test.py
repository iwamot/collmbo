import pytest

from app.tools_logic import (
    DecodedToolCall,
    RejectedToolCall,
    collect_tool_names,
    decode_tool_call,
    format_rejected_tool_calls,
    load_classic_tools,
    split_classic_tools_by_mcp_collision,
    split_classic_tools_by_reserved_name,
)


@pytest.mark.parametrize(
    "module_name, expected",
    [
        (
            "examples.tools",
            [
                {
                    "type": "function",
                    "function": {
                        "name": "get_current_weather",
                        "description": "Get the current weather in a given location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The city and state, e.g. San Francisco, CA",
                                },
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                },
                            },
                            "required": ["location"],
                        },
                    },
                }
            ],
        ),
        (None, []),
    ],
)
def test_load_classic_tools(module_name, expected):
    result = load_classic_tools(module_name)

    assert result == expected


def _classic_tool(name: str) -> dict:
    return {"type": "function", "function": {"name": name}}


@pytest.mark.parametrize(
    "tools, expected_usable, expected_colliding",
    [
        ([], [], []),
        (
            [_classic_tool("get_weather"), _classic_tool("search_repositories")],
            [_classic_tool("get_weather"), _classic_tool("search_repositories")],
            [],
        ),
        (
            [_classic_tool("n_0_get_weather"), _classic_tool("u_3_search")],
            [],
            [_classic_tool("n_0_get_weather"), _classic_tool("u_3_search")],
        ),
        (
            [_classic_tool("get_weather"), _classic_tool("b_2_run")],
            [_classic_tool("get_weather")],
            [_classic_tool("b_2_run")],
        ),
        (
            [{"type": "function", "function": {}}],
            [{"type": "function", "function": {}}],
            [],
        ),
    ],
)
def test_split_classic_tools_by_mcp_collision(
    tools, expected_usable, expected_colliding
):
    usable, colliding = split_classic_tools_by_mcp_collision(tools)

    assert usable == expected_usable
    assert colliding == expected_colliding


@pytest.mark.parametrize(
    "tools, reserved_name, expected_usable, expected_colliding",
    [
        ([], "reserved", [], []),
        (
            [_classic_tool("get_weather"), _classic_tool("search")],
            "reserved",
            [_classic_tool("get_weather"), _classic_tool("search")],
            [],
        ),
        (
            [_classic_tool("get_weather"), _classic_tool("reserved")],
            "reserved",
            [_classic_tool("get_weather")],
            [_classic_tool("reserved")],
        ),
        (
            [{"type": "function", "function": {}}],
            "reserved",
            [{"type": "function", "function": {}}],
            [],
        ),
    ],
)
def test_split_classic_tools_by_reserved_name(
    tools, reserved_name, expected_usable, expected_colliding
):
    usable, colliding = split_classic_tools_by_reserved_name(tools, reserved_name)

    assert usable == expected_usable
    assert colliding == expected_colliding


def test_collect_tool_names():
    tools = [
        {"type": "function", "function": {"name": "get_current_weather"}},
        {"type": "function", "function": {"name": "n_0_search"}},
        {"type": "function"},
    ]
    assert collect_tool_names(tools) == frozenset(
        {"get_current_weather", "n_0_search", ""}
    )


TOOL_NAMES = frozenset({"get_current_weather", "n_0_search"})


@pytest.mark.parametrize(
    "name, arguments, expected",
    [
        (
            "get_current_weather",
            '{"location": "Tokyo"}',
            DecodedToolCall(arguments={"location": "Tokyo"}),
        ),
        ("n_0_search", "{}", DecodedToolCall(arguments={})),
        (
            "get_weather",
            '{"location": "Tokyo"}',
            RejectedToolCall(reason="Unknown tool: get_weather"),
        ),
        ("", "{}", RejectedToolCall(reason="Unknown tool: ")),
        (
            "get_current_weather",
            '{"location": ',
            RejectedToolCall(
                reason="Invalid arguments for get_current_weather: "
                "Expecting value: line 1 column 14 (char 13)"
            ),
        ),
        (
            "get_current_weather",
            '["Tokyo"]',
            RejectedToolCall(
                reason="Invalid arguments for get_current_weather: "
                "expected a JSON object"
            ),
        ),
    ],
)
def test_decode_tool_call(name, arguments, expected):
    result = decode_tool_call(name=name, arguments=arguments, tool_names=TOOL_NAMES)
    assert result == expected


@pytest.mark.parametrize(
    "reasons, expected",
    [
        (
            ["Unknown tool: get_weather"],
            "The model kept calling tools it cannot use. Unknown tool: get_weather",
        ),
        (
            ["Unknown tool: a", "Invalid arguments for b: expected a JSON object"],
            (
                "The model kept calling tools it cannot use. Unknown tool: a; "
                "Invalid arguments for b: expected a JSON object"
            ),
        ),
    ],
)
def test_format_rejected_tool_calls(reasons, expected):
    assert format_rejected_tool_calls(reasons) == expected
