import json
from copy import deepcopy
from itertools import product

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


TOOL_NAMES = frozenset({"get_current_weather", "n_0_search"})


def test_tool_partitions_preserve_every_definition_and_its_relative_order():
    kinds = (
        ({"function": {"name": "get_weather"}}, False, "get_weather"),
        ({"function": {"name": "reserved"}}, False, "reserved"),
        ({"function": {"name": "n_0_get_weather"}}, True, "n_0_get_weather"),
        ({"function": {"name": "u_3_search"}}, True, "u_3_search"),
        ({"function": {"name": "b_2_run"}}, True, "b_2_run"),
        ({"function": {}}, False, ""),
        ({}, False, ""),
    )
    for size in range(4):
        for selected in product(kinds, repeat=size):
            tools: list[dict] = []
            for i, (definition, _, _) in enumerate(selected):
                tool: dict = deepcopy(definition) | {"type": "function"}
                if "function" in tool:
                    tool["function"]["description"] = f"definition {i}"
                tools.append(tool)
            before = deepcopy(tools)
            assert collect_tool_names(tools) == frozenset(
                name for _, _, name in selected
            )
            assert split_classic_tools_by_mcp_collision(tools) == (
                [
                    tool
                    for tool, (_, collides, _) in zip(tools, selected, strict=True)
                    if not collides
                ],
                [
                    tool
                    for tool, (_, collides, _) in zip(tools, selected, strict=True)
                    if collides
                ],
            )
            for reserved in ("reserved", "get_weather", "n_0_get_weather"):
                assert split_classic_tools_by_reserved_name(tools, reserved) == (
                    [
                        tool
                        for tool, (_, _, name) in zip(tools, selected, strict=True)
                        if name != reserved
                    ],
                    [
                        tool
                        for tool, (_, _, name) in zip(tools, selected, strict=True)
                        if name == reserved
                    ],
                )
            assert tools == before


def test_offered_tool_arguments_preserve_json_values_without_coercion():
    values = (
        None,
        True,
        False,
        0,
        1,
        42,
        "",
        "Tokyo 日本語\n",
        ["a", None],
        {"nested": [True, 1]},
    )
    for name, first, second, ascii_only in product(
        TOOL_NAMES, values, values, (False, True)
    ):
        arguments = {"first": first, "second": second}
        encoded = json.dumps(arguments, ensure_ascii=ascii_only)
        result = decode_tool_call(name=name, arguments=encoded, tool_names=TOOL_NAMES)
        assert isinstance(result, DecodedToolCall)
        assert json.dumps(result.arguments, sort_keys=True) == json.dumps(
            arguments, sort_keys=True
        )
    for name in TOOL_NAMES:
        assert decode_tool_call(
            name=name, arguments="{}", tool_names=TOOL_NAMES
        ) == DecodedToolCall(arguments={})


@pytest.mark.parametrize(
    "name, arguments, expected",
    [
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
                reason="Invalid arguments for get_current_weather: Expecting value: line 1 column 14 (char 13)"
            ),
        ),
        (
            "get_current_weather",
            '["Tokyo"]',
            RejectedToolCall(
                reason="Invalid arguments for get_current_weather: expected a JSON object"
            ),
        ),
    ],
)
def test_rejected_tool_calls_explain_why_they_cannot_be_dispatched(
    name, arguments, expected
):
    assert (
        decode_tool_call(name=name, arguments=arguments, tool_names=TOOL_NAMES)
        == expected
    )


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
