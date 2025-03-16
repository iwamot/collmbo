import base64
import logging
from typing import Optional

from app.slack_file_download_ops import download_slack_file_content


def get_pdf_content_if_exists(
    *,
    bot_token: str,
    files: Optional[list[dict]],
    logger: logging.Logger,
) -> list[dict]:
    content: list[dict] = []
    if not files:
        return content

    for file in files:
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

            image_url_item = {
                "type": "image_url",
                "image_url": {"url": f"data:application/pdf;base64,{encoded_pdf}"},
            }
            content.append(image_url_item)

    return content


# Bedrock Claude allows up to 5 PDFs, so remove the oldest ones if over the limit
def trim_pdf_content(messages: list[dict]) -> None:
    def count_pdfs() -> int:
        return sum(
            1
            for message in messages
            if isinstance(message.get("content"), list)
            for item in message["content"]
            if item["type"] == "image_url"
            and item["image_url"]["url"].startswith("data:application/pdf;")
        )

    while count_pdfs() > 5:
        for message in messages:
            if not isinstance(message.get("content"), list):
                continue
            for item in message["content"]:
                if item["type"] == "image_url" and item["image_url"]["url"].startswith(
                    "data:application/pdf;"
                ):
                    message["content"].remove(item)
                    break
            else:
                continue
            break
