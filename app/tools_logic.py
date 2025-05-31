"""
This module provides logical functions for tools.
"""

from importlib import import_module
from typing import Optional

from strands.types.tools import ToolSpec


def load_classic_tools(module_name: Optional[str]) -> list[dict]:
    """
    Load tools from a module.

    Args:
        module_name (Optional[str]): The name of the module to load tools from.

    Returns:
        list[dict]: The loaded tools, or an empty list if none.
    """
    return import_module(module_name).tools if module_name is not None else []


def transform_mcp_spec_to_classic_tool(mcp_spec: ToolSpec) -> dict:
    """
    Transform an MCP tool specification to a classic tool format.

    Args:
        mcp_spec (dict): The MCP tool specification.

    Returns:
        dict: The transformed tool in classic format.
    """
    return {
        "type": "function",
        "function": {
            "name": mcp_spec["name"],
            "description": mcp_spec["description"],
            "parameters": mcp_spec["inputSchema"]["json"],
        },
    }


def find_tool_by_name(tools: list[dict], tool_name: str) -> Optional[dict]:
    """
    Find a tool by its name in a list of tools.

    Args:
        tools (list[dict]): A list of tools.
        tool_name (str): The name of the tool to find.

    Returns:
        Optional[dict]: The tool with the specified name, or None if not found.
    """
    return next(
        (tool for tool in tools if tool.get("function", {}).get("name") == tool_name),
        None,
    )
