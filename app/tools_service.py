"""
This module provides service functions for tools.
"""

import json
import logging
from importlib import import_module
from types import ModuleType
from typing import Any

from litellm.types.utils import ChatCompletionMessageToolCall, Message
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPAgentTool
from strands.tools.mcp.mcp_client import MCPClient

from app.env import LITELLM_TOOLS_MODULE_NAME, MCP_SERVER_URL
from app.message_logic import build_tool_message
from app.tools_logic import find_tool_by_name, transform_mcp_spec_to_classic_tool


def create_streamable_http_transport() -> Any:
    """
    Creates a streamable HTTP transport for the MCP client.

    Returns:
        Any: The streamable HTTP client for the MCP server.
    """
    if MCP_SERVER_URL is None:
        raise ValueError("MCP_SERVER_URL cannot be None")
    return streamablehttp_client(MCP_SERVER_URL)


def load_mcp_tools() -> list[dict]:
    """
    Loads MCP tools from the MCP server.

    Returns:
        list[dict]: A list of MCP tools transformed to classic tool format.
    """
    if MCP_SERVER_URL is None:
        return []
    mcp_client = MCPClient(create_streamable_http_transport)
    with mcp_client:
        return transform_mcp_tools_to_classic_tools(mcp_client.list_tools_sync())


def transform_mcp_tools_to_classic_tools(mcp_tools: list[MCPAgentTool]) -> list[dict]:
    """
    Transform MCP tools to classic tool format.

    Args:
        mcp_tools (list[MCPAgentTool]): A list of MCPAgentTool instances.

    Returns:
        list[dict]: A list of dictionaries representing the tools in classic format.
    """
    return [
        transform_mcp_spec_to_classic_tool(mcp_tool.tool_spec) for mcp_tool in mcp_tools
    ]


def process_tool_calls(
    *,
    classic_tools: list[dict],
    mcp_tools: list[dict],
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
    assistant_message["tool_calls"] = response_message.model_dump()["tool_calls"]
    for tool_call in response_message.tool_calls:
        process_tool_call(
            classic_tools=classic_tools,
            mcp_tools=mcp_tools,
            tool_call=tool_call,
            messages=messages,
            logger=logger,
        )


def process_tool_call(
    *,
    classic_tools: list[dict],
    mcp_tools: list[dict],
    tool_call: ChatCompletionMessageToolCall,
    messages: list[dict],
    logger: logging.Logger,
) -> None:
    """
    Processes a single tool call and updates the messages list.

    Args:
        tool_call (ChatCompletionMessageToolCall): The tool call to process.
        messages (list[dict]): The list of messages to include in the reply.
        logger (logging.Logger): The logger instance.

    Returns:
        None
    """
    tool_name = tool_call.function.name
    if tool_name is None:
        logger.warning(
            "Skipped a tool call due to missing tool name. Tool call details: %s",
            tool_call,
        )
        return

    classic_tool = find_tool_by_name(classic_tools, tool_name)
    if classic_tool is not None and LITELLM_TOOLS_MODULE_NAME is not None:
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

    mcp_tool = find_tool_by_name(mcp_tools, tool_name)
    if mcp_tool is not None:
        mcp_client = MCPClient(create_streamable_http_transport)
        with mcp_client:
            tool_response = process_mcp_tool_call(
                mcp_client=mcp_client,
                tool_call_id=tool_call.id,
                tool_name=tool_name,
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
