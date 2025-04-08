"""
This module contains utility functions for the Slack Bolt application framework.
"""

from typing import Optional

from slack_bolt import BoltContext


def extract_user_id_from_context(context: BoltContext) -> Optional[str]:
    """
    Extract the user ID from a Bolt context object.

    Args:
        context (BoltContext): The Bolt context object.
    Returns:
        Optional[str]: The user ID if available, None otherwise.
    """
    return context.actor_user_id or context.user_id
