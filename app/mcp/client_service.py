"""
Service functions shared by the MCP clients that collmbo opens.
"""

from strands.tools.mcp.mcp_agent_tool import MCPAgentTool
from strands.tools.mcp.mcp_client import MCPClient


def list_all_tools(client: MCPClient) -> list[MCPAgentTool]:
    """
    List every tool an MCP server exposes, following its pagination.

    A server may split tools/list into pages; reading only the first page would
    drop the rest without any error.

    Args:
        client (MCPClient): A started MCP client.

    Returns:
        list[MCPAgentTool]: The tools from all pages, in the server's order.
    """
    tools: list[MCPAgentTool] = []
    token: str | None = None
    while True:
        page = client.list_tools_sync(pagination_token=token)
        tools.extend(page)
        token = page.pagination_token
        if token is None:
            return tools
