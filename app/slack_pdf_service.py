import base64
import logging
from typing import Optional

from app.slack_file_service import download_slack_file_content


def get_pdf_content_if_exists(
    *,
    bot_token: str,
    files: Optional[list[dict]],
    logger: logging.Logger,
    max_pdfs: int = 5,
    current_pdf_count: int = 0,
) -> list[dict]:
    content: list[dict] = []
    if not files:
        return content

    remaining_slots = max_pdfs - current_pdf_count
    if remaining_slots <= 0:
        return content

    for file in files:
        if len(content) >= remaining_slots:
            break
        mime_type = file.get("mimetype")
        if mime_type == "application/pdf":
            file_url = file.get("url_private")
            if file_url is None:
                logger.warning("Skipped a PDF file due to missing 'url_private'")
                continue
            pdf_bytes = download_slack_file_content(
                file_url, bot_token, ["application/pdf", "binary/octet-stream"]
            )
            if not pdf_bytes.startswith(b"%PDF-"):
                skipped_file_message = (
                    f"Skipped a file because it does not have a valid PDF header "
                    f"(url: {file_url})"
                )
                logger.warning(skipped_file_message)
                continue
            encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

            file_item = {
                "type": "file",
                "file": {
                    "filename": file.get("name"),
                    "file_data": f"data:application/pdf;base64,{encoded_pdf}",
                },
            }
            content.append(file_item)

    return content
