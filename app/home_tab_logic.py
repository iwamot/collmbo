"""
Logic functions for building home tab blocks.
"""

from typing import List

from slack_sdk.models.blocks import Block, DividerBlock, HeaderBlock, SectionBlock
from slack_sdk.models.blocks.basic_components import MarkdownTextObject, PlainTextObject


def build_home_tab_blocks(mcp_servers: list[dict[str, str]]) -> List[Block]:
    """
    Build Slack Block Kit blocks for the home tab.

    Args:
        mcp_servers (list[dict[str, str]]): List of MCP server info.

    Returns:
        List[Block]: List of Block Kit blocks.
    """
    blocks: List[Block] = []

    if not mcp_servers:
        blocks.extend(
            [
                HeaderBlock(
                    text=PlainTextObject(text="MCP Servers without Authentication")
                ),
                DividerBlock(),
                SectionBlock(
                    text=MarkdownTextObject(
                        text="No MCP servers are currently configured."
                    )
                ),
            ]
        )
        return blocks

    # Add header for MCP servers
    blocks.extend(
        [
            HeaderBlock(
                text=PlainTextObject(text="MCP Servers without Authentication")
            ),
            DividerBlock(),
        ]
    )

    # Add each server in table-like format
    for server in mcp_servers:
        blocks.append(
            SectionBlock(
                text=MarkdownTextObject(
                    text=f"• *{server['name']}* - `{server['url']}`"
                )
            )
        )

    return blocks
