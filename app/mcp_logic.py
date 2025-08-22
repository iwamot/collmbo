"""
This module provides pure logic functions for MCP configuration.
"""

from typing import Optional


def parse_mcp_config(config_data: Optional[dict]) -> dict:
    """
    Parse and validate MCP configuration data.

    Args:
        config_data (Optional[dict]): Raw configuration data from YAML.

    Returns:
        dict: Validated configuration with empty servers list if no valid config.
    """
    empty_config: dict = {"servers": []}

    if not config_data:
        return empty_config

    if not isinstance(config_data, dict) or "servers" not in config_data:
        return empty_config

    return config_data


def filter_no_auth_servers(config: dict) -> list[str]:
    """
    Extract URLs of servers with auth_type="none" from configuration.

    Args:
        config (dict): MCP configuration dictionary.

    Returns:
        list[str]: List of no-auth server URLs.
    """
    urls = []
    for server in config.get("servers", []):
        if server.get("auth_type") == "none":
            urls.append(server["url"])
    return urls


def get_server_info_from_config(config: dict) -> list[dict[str, str]]:
    """
    Extract server information for UI display from configuration.

    Args:
        config (dict): MCP configuration dictionary.

    Returns:
        list[dict[str, str]]: List of server info with 'name' and 'url' keys.
    """
    servers = []
    for server in config.get("servers", []):
        if server.get("auth_type") == "none":
            servers.append({"name": server["name"], "url": server["url"]})
    return servers
