"""
Logic functions for AgentCore Identity integration.
"""


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
