"""
Service functions for shared MCP tools integration.
"""

import logging
import os
import threading
import time
from functools import partial

from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

from app.env import LLM_MODEL
from app.mcp.config_logic import build_bearer_headers
from app.mcp.config_service import get_bearer_servers, get_no_auth_servers
from app.mcp.tools_logic import transform_mcp_spec_to_classic_tool

REFRESH_INTERVAL_SECONDS = 3600

shared_mcp_tools: list[dict] = []


def _load_server_tools(
    *,
    url: str,
    headers: dict[str, str] | None,
    auth_type: str,
    server_index: int,
) -> list[dict]:
    """
    Load and transform the tools exposed by a single MCP server.

    Args:
        url (str): The MCP server URL.
        headers (Optional[dict[str, str]]): Headers to send, or None.
        auth_type (str): The auth type to encode into tool names.
        server_index (int): The server index within its auth-type group.

    Returns:
        list[dict]: Tools in classic format.
    """
    client = MCPClient(partial(streamablehttp_client, url, headers=headers))
    with client:
        tools = client.list_tools_sync()
    return [
        transform_mcp_spec_to_classic_tool(
            mcp_spec=tool.tool_spec,
            auth_type=auth_type,
            server_index=server_index,
            model=LLM_MODEL,
        )
        for tool in tools
    ]


def load_shared_mcp_tools() -> None:
    """
    Loads tools from servers Collmbo authenticates itself (none and bearer)
    and updates the cache.
    """
    global shared_mcp_tools
    result: list[dict] = []
    for idx, server in enumerate(get_no_auth_servers()):
        url = server["url"]
        try:
            result.extend(
                _load_server_tools(
                    url=url, headers=None, auth_type="none", server_index=idx
                )
            )
        except Exception as exc:
            logging.warning("Failed to load MCP tools from %s: %s", url, exc)
    for idx, server in enumerate(get_bearer_servers()):
        url = server["url"]
        headers = build_bearer_headers(server, os.environ)
        if headers is None:
            logging.warning(
                "Skipping bearer MCP server %s: token env var %r is not set",
                server.get("name"),
                server.get("token_env"),
            )
            continue
        try:
            result.extend(
                _load_server_tools(
                    url=url, headers=headers, auth_type="bearer", server_index=idx
                )
            )
        except Exception as exc:
            logging.warning("Failed to load MCP tools from %s: %s", url, exc)
    shared_mcp_tools = result


def get_shared_mcp_tools() -> list[dict]:
    """
    Get the cached list of shared MCP tools.

    Returns:
        list[dict]: Cached shared MCP tools in classic format.
    """
    return shared_mcp_tools


def start_shared_mcp_tools_refresh_loop() -> None:
    """
    Start background thread to periodically refresh shared MCP tools.
    Performs initial load before starting the refresh loop.
    """
    load_shared_mcp_tools()

    def refresh_loop():
        """Background refresh loop for shared MCP tools."""
        while True:
            time.sleep(REFRESH_INTERVAL_SECONDS)
            load_shared_mcp_tools()
            logging.info(f"Shared MCP tools refreshed: {len(shared_mcp_tools)} tools")

    threading.Thread(
        target=refresh_loop,
        daemon=True,
        name="shared-mcp-tools-refresh",
    ).start()


def process_shared_mcp_tool_call(
    *,
    server_url: str,
    tool_call_id: str,
    tool_name: str,
    arguments: dict,
    headers: dict[str, str] | None = None,
) -> str:
    """
    Processes a shared MCP tool call by creating an MCP client.

    Args:
        server_url (str): The URL of the MCP server.
        tool_call_id (str): The ID of the tool call.
        tool_name (str): The name of the tool to call.
        arguments (dict): The arguments to pass to the function.
        headers (Optional[dict[str, str]]): Headers to send (e.g. a bearer
            Authorization header), or None for no-auth servers.

    Returns:
        str: The response from the tool call.
    """
    mcp_client = MCPClient(lambda: streamablehttp_client(server_url, headers=headers))
    with mcp_client:
        result = mcp_client.call_tool_sync(
            tool_use_id=tool_call_id,
            name=tool_name,
            arguments=arguments,
        )
    content = result["content"][0]
    return content.get("text", "")
