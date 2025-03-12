from typing import Optional, Sequence

from app.env import IMAGE_FILE_ACCESS_ENABLED, PDF_FILE_ACCESS_ENABLED


def can_send_image_url_to_litellm(bot_scopes: Optional[Sequence[str]]) -> bool:
    if IMAGE_FILE_ACCESS_ENABLED is False:
        return False
    if bot_scopes is None:
        return False
    return "files:read" in bot_scopes


def can_send_pdf_url_to_litellm(bot_scopes: Optional[Sequence[str]]) -> bool:
    if PDF_FILE_ACCESS_ENABLED is False:
        return False
    if bot_scopes is None:
        return False
    return "files:read" in bot_scopes
