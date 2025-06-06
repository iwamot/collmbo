import pytest
from strands.types.tools import ToolSpec

from app.tools_logic import (
    build_mcp_tool_name,
    is_mcp_tool_name,
    load_classic_tools,
    parse_mcp_tool_name,
    split_mcp_server_url,
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
    "env_value, expected",
    [
        ("http://a|http://b", ["http://a", "http://b"]),
        ("single_url", ["single_url"]),
        ("", []),
        (None, []),
    ],
)
def test_split_mcp_server_url(env_value, expected):
    result = split_mcp_server_url(env_value)

    assert result == expected


@pytest.mark.parametrize(
    "spec_name, server_index, expected",
    [
        ("add", 0, "add-0"),
        ("echo", 1, "echo-1"),
        ("complex_name", 42, "complex_name-42"),
    ],
)
def test_build_mcp_tool_name(spec_name: str, server_index: int, expected: str):
    result = build_mcp_tool_name(spec_name, server_index)

    assert result == expected


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        ("add-0", ("add", 0)),
        ("echo-12", ("echo", 12)),
        ("complex_name-42", ("complex_name", 42)),
    ],
)
def test_parse_mcp_tool_name(tool_name: str, expected: tuple[str, int]):
    result = parse_mcp_tool_name(tool_name)

    assert result == expected


@pytest.mark.parametrize(
    "mcp_spec, server_index, expected",
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
            0,
            {
                "type": "function",
                "function": {
                    "name": "add-0",
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
            1,
            {
                "type": "function",
                "function": {
                    "name": "echo-1",
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
def test_transform_mcp_spec_to_classic_tool(
    mcp_spec: ToolSpec,
    server_index: int,
    expected: dict,
):
    result = transform_mcp_spec_to_classic_tool(mcp_spec, server_index)

    assert result == expected


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        ("add-0", True),
        ("echo-12", True),
        ("classic", False),
        ("send_email", False),
    ],
)
def test_is_mcp_tool_name(tool_name: str, expected: bool):
    result = is_mcp_tool_name(tool_name)

    assert result == expected
