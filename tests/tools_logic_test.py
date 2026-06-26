import pytest

from app.tools_logic import (
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
