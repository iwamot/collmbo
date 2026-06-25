"""
Tests for MCP tools logic module.
"""

import pytest

from app.mcp.oauth_tools_logic import parse_mcp_tool_name
from app.mcp.tools_logic import build_mcp_tool_name, transform_mcp_spec_to_classic_tool
from app.tools_logic import is_mcp_tool_name


@pytest.mark.parametrize(
    "spec_name, auth_type, server_index, expected",
    [
        ("tool1", "none", 0, "n_0_tool1"),
        ("tool2", "user_federation", 1, "u_1_tool2"),
        ("tool4", "bearer", 3, "b_3_tool4"),
        ("tool3", "unknown", 2, "unknown_2_tool3"),
        ("tool5", "none", 12, "n_12_tool5"),
        ("get_weather", "bearer", 0, "b_0_get_weather"),
    ],
)
def test_build_mcp_tool_name(spec_name, auth_type, server_index, expected):
    result = build_mcp_tool_name(spec_name, auth_type, server_index)

    assert result == expected


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        ("n_0_tool1", ("tool1", "none", 0)),
        ("u_1_tool2", ("tool2", "user_federation", 1)),
        ("b_3_tool4", ("tool4", "bearer", 3)),
        ("u_2_my-complex-tool", ("my-complex-tool", "user_federation", 2)),
        # Spec names containing the separator round-trip correctly
        ("u_2_get_user_info", ("get_user_info", "user_federation", 2)),
        # Server index with multiple digits
        ("n_10_tool5", ("tool5", "none", 10)),
    ],
)
def test_parse_mcp_tool_name(tool_name, expected):
    result = parse_mcp_tool_name(tool_name)

    assert result == expected


@pytest.mark.parametrize(
    "tool_name",
    [
        "tool1",
        "tool1_n",
        "x_0_tool1",
        "n_abc_tool1",
    ],
)
def test_parse_mcp_tool_name_errors(tool_name):
    result = parse_mcp_tool_name(tool_name)
    assert result == ("", "", -1)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("n_0_tool1", True),
        ("u_1_tool2", True),
        ("b_3_tool4", True),
        ("n_10_tool5", True),
        ("tool3", False),
        ("", False),
        # Classic tool names with underscores are not misdetected as MCP
        ("get_weather", False),
        # Unrecognized auth abbreviation
        ("x_0_tool1", False),
        # Non-numeric server index
        ("n_abc_tool1", False),
    ],
)
def test_is_mcp_tool_name(name, expected):
    result = is_mcp_tool_name(name)

    assert result == expected


@pytest.mark.parametrize(
    "mcp_spec, auth_type, server_index, model, expected",
    [
        (
            {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    }
                },
            },
            "none",
            0,
            "gpt-4",
            {
                "type": "function",
                "function": {
                    "name": "n_0_test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    },
                },
            },
        ),
        (
            {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string", "format": "invalid"}
                        },
                    }
                },
            },
            "none",
            0,
            "gemini/gemini-pro",
            {
                "type": "function",
                "function": {
                    "name": "n_0_test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    },
                },
            },
        ),
        (
            {
                "name": "test_tool",
                "description": "Test tool",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string", "format": "date-time"}
                        },
                    }
                },
            },
            "none",
            0,
            "gemini/gemini-pro",
            {
                "type": "function",
                "function": {
                    "name": "n_0_test_tool",
                    "description": "Test tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param": {"type": "string", "format": "date-time"}
                        },
                    },
                },
            },
        ),
        (
            {
                "name": "test_tool",
                "description": "Test tool without type",
                "inputSchema": {"json": {"properties": {"param": {"type": "string"}}}},
            },
            "none",
            0,
            "gpt-4",
            {
                "type": "function",
                "function": {
                    "name": "n_0_test_tool",
                    "description": "Test tool without type",
                    "parameters": {
                        "type": "object",
                        "properties": {"param": {"type": "string"}},
                    },
                },
            },
        ),
        (
            {
                "name": "test_tool",
                "description": "Test tool without properties",
                "inputSchema": {"json": {"type": "object"}},
            },
            "none",
            0,
            "gpt-4",
            {
                "type": "function",
                "function": {
                    "name": "n_0_test_tool",
                    "description": "Test tool without properties",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ),
    ],
)
def test_transform_mcp_spec_to_classic_tool(
    mcp_spec, auth_type, server_index, model, expected
):
    result = transform_mcp_spec_to_classic_tool(
        mcp_spec=mcp_spec,
        auth_type=auth_type,
        server_index=server_index,
        model=model,
    )

    assert result == expected
