"""
This module provides logical functions for tools.
"""

import json
from dataclasses import dataclass
from importlib import import_module

from app.mcp.tools_logic import (
    AUTH_TYPE_ABBREVIATIONS,
    MCP_TOOL_NAME_SEPARATOR,
)

ABBREVIATION_TO_AUTH_TYPE = {v: k for k, v in AUTH_TYPE_ABBREVIATIONS.items()}


def is_mcp_tool_name(name: str) -> bool:
    """
    Check if a tool name indicates it is an MCP tool.

    Args:
        name (str): The name of the tool.

    Returns:
        bool: True if the tool is an MCP tool, False otherwise.
    """
    # An MCP tool name has the structure "{auth_abbrev}_{server_index}_{spec_name}".
    parts = name.split(MCP_TOOL_NAME_SEPARATOR)
    if len(parts) < 3:
        return False
    auth_abbrev, server_index = parts[0], parts[1]
    return auth_abbrev in ABBREVIATION_TO_AUTH_TYPE and server_index.isdigit()


def split_classic_tools_by_mcp_collision(
    tools: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Partition classic tools by whether their name collides with the MCP tool
    naming scheme.

    A classic tool whose name is shaped like an MCP tool name would be
    misrouted to an MCP server instead of being called as a classic tool.

    Args:
        tools (list[dict]): Classic tools in OpenAI tool format.

    Returns:
        tuple[list[dict], list[dict]]: (usable tools, colliding tools).
    """
    usable: list[dict] = []
    colliding: list[dict] = []
    for tool in tools:
        name = tool.get("function", {}).get("name", "")
        if is_mcp_tool_name(name):
            colliding.append(tool)
        else:
            usable.append(tool)
    return usable, colliding


def split_classic_tools_by_reserved_name(
    tools: list[dict],
    reserved_name: str,
) -> tuple[list[dict], list[dict]]:
    """
    Partition classic tools by whether their name matches a reserved tool name.

    A classic tool that reuses a reserved name would be misrouted to the built-in
    tool that owns that name instead of being called as a classic tool.

    Args:
        tools (list[dict]): Classic tools in OpenAI tool format.
        reserved_name (str): The reserved tool name.

    Returns:
        tuple[list[dict], list[dict]]: (usable tools, colliding tools).
    """
    usable: list[dict] = []
    colliding: list[dict] = []
    for tool in tools:
        name = tool.get("function", {}).get("name", "")
        if name == reserved_name:
            colliding.append(tool)
        else:
            usable.append(tool)
    return usable, colliding


def load_classic_tools(module_name: str | None) -> list[dict]:
    """
    Load tools from a module.

    Args:
        module_name (Optional[str]): The name of the module to load tools from.

    Returns:
        list[dict]: The loaded tools, or an empty list if none.
    """
    return import_module(module_name).tools if module_name is not None else []


@dataclass(frozen=True)
class DecodedToolCall:
    """A tool call whose name is offered to the model and whose arguments parsed."""

    arguments: dict


@dataclass(frozen=True)
class RejectedToolCall:
    """A tool call that cannot be dispatched; `reason` goes back to the model."""

    reason: str


class RejectedToolCallsError(RuntimeError):
    """Raised when the model keeps issuing tool calls that cannot be dispatched."""


def collect_tool_names(tools: list[dict]) -> frozenset[str]:
    """
    Collect the names of the tools offered to the model.

    Args:
        tools (list[dict]): Tools in OpenAI tool format.

    Returns:
        frozenset[str]: The tool names.
    """
    return frozenset(tool.get("function", {}).get("name", "") for tool in tools)


def decode_tool_call(
    *,
    name: str,
    arguments: str,
    tool_names: frozenset[str],
) -> DecodedToolCall | RejectedToolCall:
    """
    Decide whether a tool call from the model can be dispatched.

    A model may call a tool that was never offered to it or emit arguments that
    are not a JSON object. Such a call is answered with a tool message
    describing the problem so the model can correct itself, instead of being
    dispatched.

    Args:
        name (str): The tool name the model called.
        arguments (str): The raw JSON arguments from the model.
        tool_names (frozenset[str]): The names of the tools offered to the model.

    Returns:
        DecodedToolCall | RejectedToolCall: The parsed arguments, or the reason
        the call is rejected.
    """
    if name not in tool_names:
        return RejectedToolCall(reason=f"Unknown tool: {name}")
    try:
        parsed = json.loads(arguments)
    except json.JSONDecodeError as e:
        return RejectedToolCall(reason=f"Invalid arguments for {name}: {e}")
    if not isinstance(parsed, dict):
        return RejectedToolCall(
            reason=f"Invalid arguments for {name}: expected a JSON object"
        )
    return DecodedToolCall(arguments=parsed)


def format_rejected_tool_calls(reasons: list[str]) -> str:
    """
    Build the error message for a reply abandoned over rejected tool calls.

    Args:
        reasons (list[str]): The rejection reasons of the final round.

    Returns:
        str: The message shown to the user.
    """
    return "The model kept calling tools it cannot use. " + "; ".join(reasons)
