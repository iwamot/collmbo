"""
This module provides service functions for MCP configuration.
"""

from pathlib import Path
from typing import Optional

import yaml

from app.mcp_logic import (
    filter_no_auth_servers,
    get_server_info_from_config,
    parse_mcp_config,
)

CONFIG_FILE_PATH = "config/mcp.yaml"

# Global config cache
_cached_config: Optional[dict] = None


def load_mcp_config_from_file(config_path: str = CONFIG_FILE_PATH) -> dict:
    """
    Load MCP configuration from YAML file.

    Args:
        config_path (str): Path to the YAML configuration file.

    Returns:
        dict: Parsed and validated configuration.
    """
    path = Path(config_path)

    if not path.exists():
        return parse_mcp_config(None)

    try:
        with open(path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            return parse_mcp_config(config_data)
    except Exception:
        return parse_mcp_config(None)


def get_mcp_config() -> dict:
    """
    Get the cached MCP configuration, loading it if necessary.

    Returns:
        dict: The MCP configuration.
    """
    global _cached_config
    if _cached_config is None:
        _cached_config = load_mcp_config_from_file()
    return _cached_config


def get_no_auth_servers() -> list[str]:
    """
    Get list of no-auth MCP server URLs.

    Returns:
        list[str]: List of MCP server URLs with auth_type="none".
    """
    config = get_mcp_config()
    return filter_no_auth_servers(config)


def get_server_info() -> list[dict[str, str]]:
    """
    Get server information for UI display.

    Returns:
        list[dict[str, str]]: List of server info dictionaries.
    """
    config = get_mcp_config()
    return get_server_info_from_config(config)
