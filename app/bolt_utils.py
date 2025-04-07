from typing import Optional

from slack_bolt import BoltContext


def extract_user_id_from_context(context: BoltContext) -> Optional[str]:
    return context.actor_user_id or context.user_id
