"""
Tests for the MCP no-auth logic module.
"""

import pytest

from app.mcp.config_logic import get_no_auth_servers_from_config


@pytest.mark.parametrize(
    "config, expected",
    [
        ({}, []),
        ({"servers": []}, []),
        (
            {
                "servers": [
                    {
                        "name": "Server1",
                        "url": "http://localhost:8000",
                        "auth_type": "none",
                    },
                ]
            },
            [{"name": "Server1", "url": "http://localhost:8000"}],
        ),
        (
            {
                "servers": [
                    {
                        "name": "Server1",
                        "url": "http://localhost:8000",
                        "auth_type": "oauth",
                    },
                ]
            },
            [],
        ),
        (
            {
                "servers": [
                    {
                        "name": "Server1",
                        "url": "http://localhost:8000",
                        "auth_type": "none",
                    },
                    {
                        "name": "Server2",
                        "url": "http://localhost:8001",
                        "auth_type": "oauth",
                    },
                    {
                        "name": "Server3",
                        "url": "http://localhost:8002",
                        "auth_type": "none",
                    },
                ]
            },
            [
                {"name": "Server1", "url": "http://localhost:8000"},
                {"name": "Server3", "url": "http://localhost:8002"},
            ],
        ),
    ],
)
def test_get_no_auth_servers(config, expected):
    result = get_no_auth_servers_from_config(config)

    assert result == expected
