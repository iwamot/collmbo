"""
Logic functions for AgentCore Identity integration.
"""

from typing import Optional


def create_agentcore_user_id(slack_user_id: str, random_suffix: str) -> str:
    """
    Generate user ID for AgentCore Identity with random suffix.

    Args:
        slack_user_id (str): The Slack user ID.
        random_suffix (str): Random suffix to ensure uniqueness and avoid caching.

    Returns:
        str: User ID for AgentCore in format: {slack_user_id}_{random_suffix}.
    """
    return f"{slack_user_id}_{random_suffix}"


def normalize_agentcore_config(server: dict) -> Optional[dict]:
    """
    Normalize AgentCore configuration from server config.

    Args:
        server (dict): Server configuration from mcp.yml.

    Returns:
        Optional[dict]: AgentCore config if valid, None otherwise.
    """
    if not server.get("agentcore_identity"):
        return None
    agentcore = server["agentcore_identity"]
    if not agentcore.get("region") or not agentcore.get("provider_name"):
        return None
    return {
        "region": agentcore["region"],
        "provider_name": agentcore["provider_name"],
        "scopes": server.get("scopes", []),
    }
