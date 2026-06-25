"""
This module provides service functions for tools.
"""

import json
import logging
import os
from importlib import import_module
from types import ModuleType

from litellm.types.utils import ChatCompletionMessageToolCall, Message

from app.env import TOOLS_MODULE_NAME
from app.mcp.config_logic import build_bearer_headers
from app.mcp.config_service import get_bearer_servers, get_no_auth_servers
from app.mcp.oauth_tools_logic import parse_mcp_tool_name
from app.mcp.oauth_tools_service import (
    expire_old_oauth_sessions,
    get_flattened_user_oauth_mcp_tools,
    process_oauth_mcp_tool_call,
)
from app.mcp.shared_tools_service import (
    get_shared_mcp_tools,
    process_shared_mcp_tool_call,
)
from app.message_logic import build_tool_message
from app.tools_logic import (
    is_mcp_tool_name,
    load_classic_tools,
    split_classic_tools_by_mcp_collision,
)

classic_tools: list[dict] | None = None


def get_classic_tools() -> list[dict]:
    """
    Get classic tools with lazy loading and caching.

    Returns:
        list[dict]: Cached classic tools.
    """
    global classic_tools
    if classic_tools is None:
        usable, colliding = split_classic_tools_by_mcp_collision(
            load_classic_tools(TOOLS_MODULE_NAME)
        )
        for tool in colliding:
            logging.warning(
                "Skipping classic tool %r: its name collides with the MCP tool "
                "naming scheme and would be misrouted to an MCP server.",
                tool.get("function", {}).get("name", ""),
            )
        classic_tools = usable
    return classic_tools


def get_all_tools(
    channel: str | None = None,
    user_id: str | None = None,
) -> list[dict]:
    """
    Retrieves all tools, including classic and MCP tools.
    For DM conversations, also includes authenticated MCP tools.

    Args:
        channel (Optional[str]): Slack channel ID.
        user_id (Optional[str]): User ID for authenticated tools.

    Returns:
        list[dict]: A list of all tools.
    """
    tools = get_classic_tools() + get_shared_mcp_tools()

    # Add authenticated MCP tools only for DM conversations
    # DM channels start with 'D' (direct message)
    if channel and channel.startswith("D") and user_id:
        # Remove expired sessions before getting OAuth tools
        expire_old_oauth_sessions(user_id)
        oauth_mcp_tools = get_flattened_user_oauth_mcp_tools(user_id)
        tools.extend(oauth_mcp_tools)

    return tools


def process_tool_calls(
    *,
    response_message: Message,
    assistant_message: dict,
    messages: list[dict],
    user_id: str | None = None,
) -> None:
    """
    Processes the tool calls in the response message.

    Args:
        response_message (Message): The response message containing tool calls.
        assistant_message (dict): The assistant message to update.
        messages (list[dict]): The list of messages to include in the reply.
        user_id (Optional[str]): User ID for authenticated tool access.

    Returns:
        None
    """
    if response_message.tool_calls is None:
        return

    assistant_message["tool_calls"] = response_message.model_dump()["tool_calls"]

    no_auth_servers = get_no_auth_servers()
    bearer_servers = get_bearer_servers()

    for tool_call in response_message.tool_calls:
        process_tool_call(
            tool_call=tool_call,
            messages=messages,
            no_auth_servers=no_auth_servers,
            bearer_servers=bearer_servers,
            user_id=user_id,
        )


def process_tool_call(
    *,
    tool_call: ChatCompletionMessageToolCall,
    messages: list[dict],
    no_auth_servers: list[dict],
    bearer_servers: list[dict],
    user_id: str | None = None,
) -> None:
    """
    Processes a single tool call and updates the messages list.

    Args:
        tool_call (ChatCompletionMessageToolCall): The tool call to process.
        messages (list[dict]): The list of messages to include in the reply.
        no_auth_servers (list[dict]): The list of no-auth MCP servers.
        bearer_servers (list[dict]): The list of bearer MCP servers.
        user_id (Optional[str]): User ID for authenticated tool access.

    Returns:
        None
    """
    tool_name = tool_call.function.name
    if not tool_name:
        logging.warning("Skipped tool call with empty name: %s", tool_call)
        return

    if not is_mcp_tool_name(tool_name) and TOOLS_MODULE_NAME is not None:
        tools_module = import_module(TOOLS_MODULE_NAME)
        tool_response = process_classic_tool_call(
            tools_module=tools_module,
            tool_name=tool_name,
            arguments=json.loads(tool_call.function.arguments),
        )
        tool_message = build_tool_message(
            tool_call_id=tool_call.id,
            name=tool_name,
            content=tool_response,
        )
        messages.append(tool_message)
        return

    spec_name, auth_type, server_index = parse_mcp_tool_name(tool_name)

    if auth_type == "user_federation" and user_id:
        tool_response = process_oauth_mcp_tool_call(
            tool_call_id=tool_call.id,
            tool_name=spec_name,
            arguments=json.loads(tool_call.function.arguments),
            user_id=user_id,
            server_index=server_index,
        )
        tool_message = build_tool_message(
            tool_call_id=tool_call.id,
            name=tool_name,
            content=tool_response,
        )
        messages.append(tool_message)
        return

    if auth_type == "bearer":
        server = bearer_servers[server_index]
        headers = build_bearer_headers(server, os.environ)
        tool_response = process_shared_mcp_tool_call(
            server_url=server["url"],
            tool_call_id=tool_call.id,
            tool_name=spec_name,
            arguments=json.loads(tool_call.function.arguments),
            headers=headers,
        )
        tool_message = build_tool_message(
            tool_call_id=tool_call.id,
            name=tool_name,
            content=tool_response,
        )
        messages.append(tool_message)
        return

    tool_response = process_shared_mcp_tool_call(
        server_url=no_auth_servers[server_index]["url"],
        tool_call_id=tool_call.id,
        tool_name=spec_name,
        arguments=json.loads(tool_call.function.arguments),
    )
    tool_message = build_tool_message(
        tool_call_id=tool_call.id,
        name=tool_name,
        content=tool_response,
    )
    messages.append(tool_message)


def process_classic_tool_call(
    *,
    tools_module: ModuleType,
    tool_name: str,
    arguments: dict,
) -> str:
    """
    Processes a classic tool call using the specified module and tool name.

    Args:
        tools_module (ModuleType): The module containing the tools.
        tool_name (str): The name of the tool to call.
        arguments (dict): The arguments to pass to the function.

    Returns:
        str: The response from the tool call.
    """
    tool_to_call = getattr(tools_module, tool_name)
    return tool_to_call(**arguments)
