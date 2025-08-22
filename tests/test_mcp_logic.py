"""
Tests for the MCP configuration logic module.
"""

import pytest

from app.mcp_logic import (
    filter_no_auth_servers,
    get_server_info_from_config,
    parse_mcp_config,
)


@pytest.mark.parametrize(
    "config_data, expected",
    [
        # Valid config
        (
            {
                "servers": [
                    {
                        "name": "Test Server",
                        "url": "https://test.example.com",
                        "auth_type": "none",
                    }
                ]
            },
            {
                "servers": [
                    {
                        "name": "Test Server",
                        "url": "https://test.example.com",
                        "auth_type": "none",
                    }
                ]
            },
        ),
        # None config - should return empty
        (
            None,
            {"servers": []},
        ),
        # Empty dict - should return empty
        (
            {},
            {"servers": []},
        ),
        # Invalid dict without servers key - should return empty
        (
            {"other_key": "value"},
            {"servers": []},
        ),
        # Not a dict - should return empty
        (
            "invalid",
            {"servers": []},
        ),
    ],
)
def test_parse_mcp_config(config_data, expected):
    result = parse_mcp_config(config_data)
    assert result == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        # Multiple servers with mixed auth types
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "none",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server 3",
                        "url": "https://server3.example.com",
                        "auth_type": "none",
                    },
                ]
            },
            ["https://server1.example.com", "https://server3.example.com"],
        ),
        # Only no-auth servers
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "none",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "none",
                    },
                ]
            },
            ["https://server1.example.com", "https://server2.example.com"],
        ),
        # No no-auth servers
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "oauth",
                    }
                ]
            },
            [],
        ),
        # Empty servers list
        ({"servers": []}, []),
        # No servers key
        ({}, []),
    ],
)
def test_filter_no_auth_servers(config, expected):
    result = filter_no_auth_servers(config)
    assert result == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        # Multiple servers with mixed auth types
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "none",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server 3",
                        "url": "https://server3.example.com",
                        "auth_type": "none",
                    },
                ]
            },
            [
                {"name": "Server 1", "url": "https://server1.example.com"},
                {"name": "Server 3", "url": "https://server3.example.com"},
            ],
        ),
        # Empty servers list
        ({"servers": []}, []),
        # No servers key
        ({}, []),
    ],
)
def test_get_server_info_from_config(config, expected):
    result = get_server_info_from_config(config)
    assert result == expected
