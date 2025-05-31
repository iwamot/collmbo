import pytest
from strands.types.tools import ToolSpec

from app.tools_logic import (
    find_tool_by_name,
    load_classic_tools,
    transform_mcp_spec_to_classic_tool,
)


@pytest.mark.parametrize(
    "module_name, expected_len",
    [
        ("examples.tools", 1),
        (None, 0),
    ],
)
def test_load_classic_tools(module_name, expected_len):
    result = load_classic_tools(module_name)

    assert len(result) == expected_len


@pytest.mark.parametrize(
    "mcp_spec, expected",
    [
        (
            {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"},
                        },
                    }
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"},
                        },
                    },
                },
            },
        ),
        (
            {
                "name": "echo",
                "description": "Echoes the input",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                    }
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "echo",
                    "description": "Echoes the input",
                    "parameters": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                    },
                },
            },
        ),
    ],
)
def test_transform_mcp_spec_to_classic_tool(mcp_spec: ToolSpec, expected: dict):
    result = transform_mcp_spec_to_classic_tool(mcp_spec)

    assert result == expected


@pytest.mark.parametrize(
    "tools, tool_name, expected",
    [
        (
            [
                {
                    "type": "function",
                    "function": {
                        "name": "foo",
                        "description": "desc",
                        "parameters": {},
                    },
                }
            ],
            "foo",
            {
                "type": "function",
                "function": {
                    "name": "foo",
                    "description": "desc",
                    "parameters": {},
                },
            },
        ),
        (
            [
                {
                    "type": "function",
                    "function": {
                        "name": "foo",
                        "description": "desc",
                        "parameters": {},
                    },
                }
            ],
            "bar",
            None,
        ),
        (
            [],
            "baz",
            None,
        ),
    ],
)
def test_find_tool_by_name(tools, tool_name, expected):
    result = find_tool_by_name(tools, tool_name)

    assert result == expected
