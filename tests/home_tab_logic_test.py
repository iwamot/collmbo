import pytest
from slack_sdk.models.blocks import DividerBlock, HeaderBlock, SectionBlock
from slack_sdk.models.blocks.basic_components import MarkdownTextObject, PlainTextObject

from app.home_tab_logic import build_home_tab_blocks


@pytest.mark.parametrize(
    "mcp_servers, expected_blocks",
    [
        (
            [],
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
            ],
        ),
        (
            [{"name": "TestServer", "url": "http://localhost:8000/mcp/"}],
            [
                HeaderBlock(
                    text=PlainTextObject(text="MCP Servers without Authentication")
                ),
                DividerBlock(),
                SectionBlock(
                    text=MarkdownTextObject(
                        text="• *TestServer* - `http://localhost:8000/mcp/`"
                    )
                ),
            ],
        ),
        (
            [
                {"name": "Server1", "url": "http://localhost:8001/mcp/"},
                {"name": "Server2", "url": "http://localhost:8002/mcp/"},
            ],
            [
                HeaderBlock(
                    text=PlainTextObject(text="MCP Servers without Authentication")
                ),
                DividerBlock(),
                SectionBlock(
                    text=MarkdownTextObject(
                        text="• *Server1* - `http://localhost:8001/mcp/`"
                    )
                ),
                SectionBlock(
                    text=MarkdownTextObject(
                        text="• *Server2* - `http://localhost:8002/mcp/`"
                    )
                ),
            ],
        ),
    ],
)
def test_build_home_tab_blocks(mcp_servers, expected_blocks):
    result = build_home_tab_blocks(mcp_servers)
    assert result == expected_blocks
