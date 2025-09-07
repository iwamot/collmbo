"""
This module provides service functions for tools.
"""

import json
import logging
import threading
import time
from importlib import import_module
from types import ModuleType
from typing import Any

from litellm.types.utils import ChatCompletionMessageToolCall, Message
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPAgentTool
from strands.tools.mcp.mcp_client import MCPClient

from app.env import LITELLM_MODEL_TYPE, LITELLM_TOOLS_MODULE_NAME
from app.message_logic import build_tool_message
from app.tools_logic import (
    is_mcp_tool_name,
    load_classic_tools,
    parse_mcp_tool_name,
    transform_mcp_spec_to_classic_tool,
)

# Tool refresh interval in seconds (1 hour)
TOOL_REFRESH_INTERVAL_SECONDS = 3600


def create_streamable_http_transport(url: str) -> Any:
    """
    Creates a streamable HTTP transport for the MCP client.

    Args:
        url (str): The URL of the MCP server.

    Returns:
        Any: The streamable HTTP client for the MCP server.
    """
    return streamablehttp_client(url)


def fetch_tools_from_mcp_server(url: str) -> list[MCPAgentTool]:
    """
    Fetches tools from the MCP server at the specified URL.

    Args:
        url (str): The URL of the MCP server.

    Returns:
        list[MCPAgentTool]: A list of MCPAgentTool instances representing the tools.
    """
    client = MCPClient(lambda: create_streamable_http_transport(url))
    with client:
        return client.list_tools_sync()


def load_mcp_tools() -> list[dict]:
    """
    Loads MCP tools from the MCP server.

    Returns:
        list[dict]: A list of MCP tools transformed to classic tool format.
    """
    from app.mcp_service import get_no_auth_servers

    result: list[dict] = []
    mcp_servers = get_no_auth_servers()
    for idx, url in enumerate(mcp_servers):
        try:
            tools = fetch_tools_from_mcp_server(url)
            result.extend(
                transform_mcp_spec_to_classic_tool(
                    mcp_spec=tool.tool_spec,
                    server_index=idx,
                    model=LITELLM_MODEL_TYPE,
                )
                for tool in tools
            )
        except Exception as exc:
            logging.warning("Failed to load MCP tools from %s: %s", url, exc)
    return result


def get_all_tools() -> list[dict]:
    """
    Retrieves all tools, including classic and MCP tools.

    Returns:
        list[dict]: A list of all tools.
    """
    return CLASSIC_TOOLS + MCP_TOOLS


def process_tool_calls(
    *,
    response_message: Message,
    assistant_message: dict,
    messages: list[dict],
    logger: logging.Logger,
) -> None:
    """
    Processes the tool calls in the response message.

    Args:
        response_message (Message): The response message containing tool calls.
        assistant_message (dict): The assistant message to update.
        messages (list[dict]): The list of messages to include in the reply.
        logger (logging.Logger): The logger instance.

    Returns:
        None
    """
    if response_message.tool_calls is None:
        return
    from app.mcp_service import get_no_auth_servers

    assistant_message["tool_calls"] = response_message.model_dump()["tool_calls"]
    mcp_servers = get_no_auth_servers()
    for tool_call in response_message.tool_calls:
        process_tool_call(
            tool_call=tool_call,
            messages=messages,
            mcp_servers=mcp_servers,
            logger=logger,
        )


def process_tool_call(
    *,
    tool_call: ChatCompletionMessageToolCall,
    messages: list[dict],
    mcp_servers: list[str],
    logger: logging.Logger,
) -> None:
    """
    Processes a single tool call and updates the messages list.

    Args:
        tool_call (ChatCompletionMessageToolCall): The tool call to process.
        messages (list[dict]): The list of messages to include in the reply.
        mcp_servers (list[str]): The list of MCP server URLs.
        logger (logging.Logger): The logger instance.

    Returns:
        None
    """
    tool_name = tool_call.function.name
    if not tool_name:
        logger.warning("Skipped tool call with empty name: %s", tool_call)
        return

    if not is_mcp_tool_name(tool_name) and LITELLM_TOOLS_MODULE_NAME is not None:
        tools_module = import_module(LITELLM_TOOLS_MODULE_NAME)
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

    spec_name, server_index = parse_mcp_tool_name(tool_name)
    mcp_client = MCPClient(
        lambda: create_streamable_http_transport(mcp_servers[server_index])
    )
    with mcp_client:
        tool_response = process_mcp_tool_call(
            mcp_client=mcp_client,
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


def process_mcp_tool_call(
    *,
    mcp_client: MCPClient,
    tool_call_id: str,
    tool_name: str,
    arguments: dict,
) -> str:
    """
    Processes a tool call using the MCP client.

    Args:
        mcp_client (MCPClient): The MCP client instance.
        tool_call_id (str): The ID of the tool call.
        tool_name (str): The name of the tool to call.
        arguments (dict): The arguments to pass to the function.

    Returns:
        str: The response from the tool call.
    """
    result = mcp_client.call_tool_sync(
        tool_use_id=tool_call_id,
        name=tool_name,
        arguments=arguments,
    )
    return result["content"][0]["text"]


CLASSIC_TOOLS = load_classic_tools(LITELLM_TOOLS_MODULE_NAME)
MCP_TOOLS = load_mcp_tools()


def _refresh_tools_loop():
    """Refresh MCP tool lists periodically in the background."""
    while True:
        # Wait before refresh (first iteration waits before initial refresh)
        time.sleep(TOOL_REFRESH_INTERVAL_SECONDS)

        global MCP_TOOLS
        MCP_TOOLS = load_mcp_tools()
        logging.info(f"MCP tools refreshed: {len(MCP_TOOLS)} tools")


threading.Thread(target=_refresh_tools_loop, daemon=True, name="tools-refresh").start()
