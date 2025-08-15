"""
This module provides logical functions for tools.
"""

from copy import deepcopy
from importlib import import_module
from typing import Optional

from strands.types.tools import ToolSpec

MCP_TOOL_NAME_SEPARATOR = "-"


def load_classic_tools(module_name: Optional[str]) -> list[dict]:
    """
    Load tools from a module.

    Args:
        module_name (Optional[str]): The name of the module to load tools from.

    Returns:
        list[dict]: The loaded tools, or an empty list if none.
    """
    return import_module(module_name).tools if module_name is not None else []


def parse_no_auth_mcp_servers(mcp_server_config: Optional[str]) -> list[str]:
    """
    Parse no-auth MCP server configuration and return list of URLs (for existing index-based access).

    Args:
        mcp_server_config (Optional[str]): Pipe-separated server configs in format "name:url|name:url".

    Returns:
        list[str]: A list of MCP server URLs in order.
    """
    if not mcp_server_config:
        return []

    urls = []
    for entry in mcp_server_config.split("|"):
        name, url = entry.split(":", 1)  # Split on first colon only
        urls.append(url)

    return urls


def get_mcp_server_info(mcp_server_config: Optional[str]) -> list[dict[str, str]]:
    """
    Parse no-auth MCP server configuration and return server info for UI display.

    Args:
        mcp_server_config (Optional[str]): Pipe-separated server configs in format "name:url|name:url".

    Returns:
        list[dict[str, str]]: A list of server info dictionaries with 'name' and 'url' keys.
    """
    if not mcp_server_config:
        return []

    servers = []
    for entry in mcp_server_config.split("|"):
        name, url = entry.split(":", 1)  # Split on first colon only
        servers.append({"name": name, "url": url})

    return servers


def build_mcp_tool_name(spec_name: str, server_index: int) -> str:
    """
    Build a name for an MCP tool based on its specification name and server index.

    Args:
        spec_name (str): The name of the tool specification.
        server_index (int): The index of the MCP server.

    Returns:
        str: The constructed tool name in the format "spec_name-server_index".
    """
    return f"{spec_name}{MCP_TOOL_NAME_SEPARATOR}{server_index}"


def parse_mcp_tool_name(tool_name: str) -> tuple[str, int]:
    """
    Parse an MCP tool name into its specification name and server index.

    Args:
        tool_name (str): The name of the MCP tool.

    Returns:
        tuple[str, int]: A tuple containing the tool specification name and server index.
    """
    spec_name, _, server_index = tool_name.rpartition(MCP_TOOL_NAME_SEPARATOR)
    return spec_name, int(server_index)


def is_mcp_tool_name(name: str) -> bool:
    """
    Check if a tool name indicates it is an MCP tool.

    Args:
        name (str): The name of the tool.

    Returns:
        bool: True if the tool is an MCP tool, False otherwise.
    """
    return MCP_TOOL_NAME_SEPARATOR in name


def transform_mcp_spec_to_classic_tool(
    *,
    mcp_spec: ToolSpec,
    server_index: int,
    model: str,
) -> dict:
    """
    Transform an MCP tool specification to a classic tool format.

    Args:
        mcp_spec (dict): The MCP tool specification.
        server_index (int): The index of the MCP server.
        model (str): The model name, used to determine if specific properties should be removed.

    Returns:
        dict: The transformed tool in classic format.
    """
    parameters = deepcopy(mcp_spec["inputSchema"]["json"])

    # Remove invalid "format" property for Gemini models
    if model.startswith("gemini/"):
        for prop in parameters.get("properties", {}).values():
            if "format" in prop and prop["format"] not in ("date-time", "enum"):
                prop.pop("format")

    return {
        "type": "function",
        "function": {
            "name": build_mcp_tool_name(mcp_spec["name"], server_index),
            "description": mcp_spec["description"],
            "parameters": parameters,
        },
    }
