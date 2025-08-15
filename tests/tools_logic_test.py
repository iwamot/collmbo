import pytest

from app.tools_logic import (
    build_mcp_tool_name,
    get_mcp_server_info,
    is_mcp_tool_name,
    load_classic_tools,
    parse_mcp_tool_name,
    parse_no_auth_mcp_servers,
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
        ("server1:http://a|server2:http://b", ["http://a", "http://b"]),
        ("single:single_url", ["single_url"]),
        ("", []),
        (None, []),
    ],
)
def test_parse_no_auth_mcp_servers(env_value, expected):
    result = parse_no_auth_mcp_servers(env_value)

    assert result == expected


@pytest.mark.parametrize(
    "env_value, expected",
    [
        (
            "server1:http://a|server2:http://b",
            [
                {"name": "server1", "url": "http://a"},
                {"name": "server2", "url": "http://b"},
            ],
        ),
        ("single:single_url", [{"name": "single", "url": "single_url"}]),
        ("", []),
        (None, []),
        (
            "Fetch:http://localhost:8000/fetch/mcp/|Terraform:http://localhost:8001/terraform/mcp/",
            [
                {
                    "name": "Fetch",
                    "url": "http://localhost:8000/fetch/mcp/",
                },
                {
                    "name": "Terraform",
                    "url": "http://localhost:8001/terraform/mcp/",
                },
            ],
        ),
    ],
)
def test_get_mcp_server_info(env_value, expected):
    result = get_mcp_server_info(env_value)

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
    "mcp_spec, server_index, model, expected",
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
            "gpt-4",
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
                        "properties": {
                            "message": {"type": "string"},
                        },
                    }
                },
            },
            1,
            "gpt-4",
            {
                "type": "function",
                "function": {
                    "name": "echo-1",
                    "description": "Echoes the input",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                        },
                    },
                },
            },
        ),
        (
            {
                "name": "fetch_url",
                "description": "Fetch URL content",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "format": "uri",
                                "description": "URL to fetch",
                            },
                            "max_length": {"type": "integer"},
                        },
                    }
                },
            },
            0,
            "gemini/1.5-pro",
            {
                "type": "function",
                "function": {
                    "name": "fetch_url-0",
                    "description": "Fetch URL content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to fetch",
                            },
                            "max_length": {"type": "integer"},
                        },
                    },
                },
            },
        ),
        (
            {
                "name": "timestamped",
                "description": "Takes a timestamp",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "created_at": {
                                "type": "string",
                                "format": "date-time",
                            }
                        },
                    }
                },
            },
            2,
            "gemini/1.5-flash",
            {
                "type": "function",
                "function": {
                    "name": "timestamped-2",
                    "description": "Takes a timestamp",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "created_at": {
                                "type": "string",
                                "format": "date-time",
                            }
                        },
                    },
                },
            },
        ),
        (
            {
                "name": "choice_input",
                "description": "Choose one of the options",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "option": {
                                "type": "string",
                                "format": "enum",
                                "enum": ["A", "B", "C"],
                            }
                        },
                    }
                },
            },
            3,
            "gemini/1.5-pro",
            {
                "type": "function",
                "function": {
                    "name": "choice_input-3",
                    "description": "Choose one of the options",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "option": {
                                "type": "string",
                                "format": "enum",
                                "enum": ["A", "B", "C"],
                            }
                        },
                    },
                },
            },
        ),
    ],
)
def test_transform_mcp_spec_to_classic_tool(
    mcp_spec,
    server_index,
    model,
    expected,
):
    result = transform_mcp_spec_to_classic_tool(
        mcp_spec=mcp_spec,
        server_index=server_index,
        model=model,
    )

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
