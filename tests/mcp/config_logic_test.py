"""
Tests for the MCP configuration logic module.
"""

import pytest

from app.mcp.config_logic import (
    build_bearer_headers,
    get_bearer_servers_from_config,
    get_no_auth_servers_from_config,
    get_oauth_server_from_config,
    get_oauth_server_index_from_config,
    get_oauth_servers_from_config,
    normalize_mcp_config,
)


@pytest.mark.parametrize(
    "config_data, expected",
    [
        # Valid config without auth_session_duration_minutes - should add default
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
                ],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
        # Valid config with auth_session_duration_minutes
        (
            {
                "servers": [
                    {
                        "name": "Test Server",
                        "url": "https://test.example.com",
                        "auth_type": "none",
                    }
                ],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
            },
            {
                "servers": [
                    {
                        "name": "Test Server",
                        "url": "https://test.example.com",
                        "auth_type": "none",
                    }
                ],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
        # Empty dict - should return empty with default
        (
            {},
            {
                "servers": [],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
        # Invalid dict without servers key - should return empty with default
        (
            {"other_key": "value"},
            {
                "servers": [],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
        # None input - should return empty with default
        (
            None,
            {
                "servers": [],
                "auth_session_duration_minutes": 30,
                "workload_name": "Collmbo",
                "agentcore_region": "us-west-2",
                "oauth_callback_url": "",
            },
        ),
    ],
)
def test_normalize_mcp_config(config_data, expected):
    result = normalize_mcp_config(config_data)
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
                        "auth_type": "user_federation",
                    },
                    {
                        "name": "Server 3",
                        "url": "https://server3.example.com",
                        "auth_type": "none",
                    },
                    {
                        "name": "Server 4",
                        "url": "https://server4.example.com",
                        "auth_type": "bearer",
                        "token_env": "SERVER4_TOKEN",
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
def test_get_no_auth_servers(config, expected):
    result = get_no_auth_servers_from_config(config)
    assert result == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        # Mixed auth types - only bearer servers are returned
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
                        "auth_type": "bearer",
                        "token_env": "SERVER2_TOKEN",
                    },
                    {
                        "name": "Server 3",
                        "url": "https://server3.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            [
                {
                    "name": "Server 2",
                    "url": "https://server2.example.com",
                    "token_env": "SERVER2_TOKEN",
                },
            ],
        ),
        # Bearer server without token_env - token_env defaults to empty string
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "bearer",
                    },
                ]
            },
            [
                {
                    "name": "Server 1",
                    "url": "https://server1.example.com",
                    "token_env": "",
                },
            ],
        ),
        # Empty servers list
        ({"servers": []}, []),
        # No servers key
        ({}, []),
    ],
)
def test_get_bearer_servers_from_config(config, expected):
    result = get_bearer_servers_from_config(config)
    assert result == expected


@pytest.mark.parametrize(
    "server, env, expected",
    [
        # Token resolves from the named env var
        (
            {"token_env": "MCP_TOKEN"},
            {"MCP_TOKEN": "secret-123"},
            {"Authorization": "Bearer secret-123"},
        ),
        # Missing token_env key
        ({}, {"MCP_TOKEN": "secret-123"}, None),
        # Empty token_env value
        ({"token_env": ""}, {"MCP_TOKEN": "secret-123"}, None),
        # Named env var is not set
        ({"token_env": "MCP_TOKEN"}, {}, None),
        # Named env var is set but empty
        ({"token_env": "MCP_TOKEN"}, {"MCP_TOKEN": ""}, None),
    ],
)
def test_build_bearer_headers(server, env, expected):
    result = build_bearer_headers(server, env)
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
                        "auth_type": "bearer",
                        "token_env": "SERVER2_TOKEN",
                    },
                    {
                        "name": "Server 3",
                        "url": "https://server3.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            [
                {
                    "name": "Server 3",
                    "url": "https://server3.example.com",
                    "auth_type": "user_federation",
                },
            ],
        ),
        # Server without auth_type (falsy value)
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "",
                    },
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
def test_get_oauth_servers_from_config(config, expected):
    result = get_oauth_servers_from_config(config)
    assert result == expected


@pytest.mark.parametrize(
    "config, server_index, expected",
    [
        # Valid index
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "user_federation",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            1,
            {
                "name": "Server 2",
                "url": "https://server2.example.com",
                "auth_type": "user_federation",
            },
        ),
        # Index 0
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "user_federation",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            0,
            {
                "name": "Server 1",
                "url": "https://server1.example.com",
                "auth_type": "user_federation",
            },
        ),
        # Negative index
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            -1,
            {},
        ),
        # Index out of range
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            2,
            {},
        ),
        # Empty config
        ({}, 0, {}),
        # No servers in config
        ({"servers": []}, 0, {}),
    ],
)
def test_get_oauth_server_from_config(config, server_index, expected):
    result = get_oauth_server_from_config(config, server_index)
    assert result == expected


@pytest.mark.parametrize(
    "config, server_name, expected",
    [
        # Server found at index 0
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "user_federation",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            "Server 1",
            0,
        ),
        # Server found at index 1
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "user_federation",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            "Server 2",
            1,
        ),
        # Server not found
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "user_federation",
                    },
                ]
            },
            "Server 2",
            None,
        ),
        # Empty servers list
        ({"servers": []}, "Server 1", None),
        # No servers key
        ({}, "Server 1", None),
        # Server with none auth_type (should not be in oauth servers)
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "none",
                    },
                ]
            },
            "Server 1",
            None,
        ),
    ],
)
def test_get_oauth_server_index_from_config(config, server_name, expected):
    result = get_oauth_server_index_from_config(config, server_name)
    assert result == expected
