import logging
import re
import time
from typing import Optional

from litellm.exceptions import Timeout
from slack_bolt import Ack, App, BoltContext, BoltResponse
from slack_bolt.request.payload_utils import is_event
from slack_sdk.web import WebClient

from app.bolt_middlewares import attach_bot_scopes
from app.env import (
    LITELLM_TEMPERATURE,
    LITELLM_TIMEOUT_SECONDS,
    SYSTEM_TEXT,
    TRANSLATE_MARKDOWN,
)
from app.i18n import translate
from app.litellm_image_ops import get_image_content_if_exists
from app.litellm_ops import (
    consume_litellm_stream_to_write_reply,
    messages_within_context_window,
    start_receiving_litellm_response,
)
from app.litellm_pdf_ops import get_pdf_content_if_exists, trim_pdf_content
from app.message_formatting import build_system_text, format_litellm_message_content
from app.sensitive_info_redaction import redact_string
from app.slack_api_ops import (
    find_parent_message,
    is_this_app_mentioned,
    post_wip_message,
    update_wip_message,
)
from app.slack_constants import DEFAULT_LOADING_TEXT, TIMEOUT_ERROR_MESSAGE
from app.slack_settings import (
    can_send_image_url_to_litellm,
    can_send_pdf_url_to_litellm,
)

#
# Listener functions
#


def just_ack(ack: Ack):
    ack()


#
# Chat with the bot
#


def respond_to_app_mention(
    context: BoltContext,
    payload: dict,
    client: WebClient,
    logger: logging.Logger,
):
    thread_ts = payload.get("thread_ts")
    if thread_ts is not None:
        parent_message = find_parent_message(client, context.channel_id, thread_ts)
        if parent_message is not None and is_this_app_mentioned(
            context.bot_user_id, parent_message
        ):
            # The message event handler will reply to this
            return

    wip_reply = None
    # Replace placeholder for Slack user ID in the system prompt
    system_text = build_system_text(
        SYSTEM_TEXT, TRANSLATE_MARKDOWN, context.bot_user_id
    )
    messages: list[dict] = [{"role": "system", "content": system_text}]

    try:
        user_id = context.actor_user_id or context.user_id
        if thread_ts is not None:
            # Mentioning the bot user in a thread
            if context.channel_id is None:
                raise ValueError("context.channel_id cannot be None")
            replies_in_thread: list[dict] = client.conversations_replies(
                channel=context.channel_id,
                ts=thread_ts,
                include_all_metadata=True,
                limit=1000,
            ).get("messages", [])
            for reply in replies_in_thread:
                reply_text = redact_string(reply.get("text") or "")
                message_text_item = {
                    "type": "text",
                    "text": f"<@{reply['user'] if 'user' in reply else reply['username']}>: "
                    + format_litellm_message_content(reply_text, TRANSLATE_MARKDOWN),
                }
                content = [message_text_item]

                if (
                    reply.get("bot_id") is None
                    and context.authorize_result is not None
                    and can_send_image_url_to_litellm(
                        context.authorize_result.bot_scopes
                    )
                ):
                    if context.bot_token is None:
                        raise ValueError("context.bot_token cannot be None")
                    content += get_image_content_if_exists(
                        bot_token=context.bot_token,
                        files=reply.get("files"),
                        logger=context.logger,
                    )

                if (
                    reply.get("bot_id") is None
                    and context.authorize_result is not None
                    and can_send_pdf_url_to_litellm(context.authorize_result.bot_scopes)
                ):
                    if context.bot_token is None:
                        raise ValueError("context.bot_token cannot be None")
                    content += get_pdf_content_if_exists(
                        bot_token=context.bot_token,
                        files=reply.get("files"),
                        logger=context.logger,
                    )

                role = (
                    "assistant"
                    if "user" in reply and reply["user"] == context.bot_user_id
                    else "user"
                )
                messages.append(
                    {
                        "role": role,
                        "content": (content if role == "user" else content[0]["text"]),
                    }
                )
        else:
            # Strip bot Slack user ID from initial message
            msg_text = re.sub(f"<@{context.bot_user_id}>\\s*", "", payload["text"])
            msg_text = redact_string(msg_text)
            message_text_item = {
                "type": "text",
                "text": f"<@{user_id}>: "
                + format_litellm_message_content(msg_text, TRANSLATE_MARKDOWN),
            }
            content = [message_text_item]

            if (
                payload.get("bot_id") is None
                and context.authorize_result is not None
                and can_send_image_url_to_litellm(context.authorize_result.bot_scopes)
            ):
                if context.bot_token is None:
                    raise ValueError("context.bot_token cannot be None")
                content += get_image_content_if_exists(
                    bot_token=context.bot_token,
                    files=payload.get("files"),
                    logger=context.logger,
                )
            if (
                payload.get("bot_id") is None
                and context.authorize_result is not None
                and can_send_pdf_url_to_litellm(context.authorize_result.bot_scopes)
            ):
                if context.bot_token is None:
                    raise ValueError("context.bot_token cannot be None")
                content += get_pdf_content_if_exists(
                    bot_token=context.bot_token,
                    files=payload.get("files"),
                    logger=context.logger,
                )

            messages.append({"role": "user", "content": content})

        loading_text = translate(
            locale=context.get("locale"), text=DEFAULT_LOADING_TEXT
        )
        if context.channel_id is None:
            raise ValueError("context.channel_id cannot be None")
        if context.user_id is None:
            raise ValueError("user_id cannot be None")
        wip_reply = post_wip_message(
            client=client,
            channel=context.channel_id,
            thread_ts=payload["ts"],
            loading_text=loading_text,
            messages=messages,
            user=context.user_id,
        )

        trim_pdf_content(messages)
        (
            messages,
            num_context_tokens,
            max_context_tokens,
        ) = messages_within_context_window(messages)
        num_messages = len([msg for msg in messages if msg.get("role") != "system"])
        if num_messages == 0:
            if context.channel_id is None:
                raise ValueError("context.channel_id cannot be None")
            if context.user_id is None:
                raise ValueError("context.user_id cannot be None")
            update_wip_message(
                client=client,
                channel=context.channel_id,
                ts=wip_reply["message"]["ts"],
                text=(
                    f":warning: The previous message is too long "
                    f"({num_context_tokens}/{max_context_tokens} prompt tokens)."
                ),
                messages=messages,
                user=context.user_id,
            )
        else:
            if context.user_id is None:
                raise ValueError("context.user_id cannot be None")
            stream = start_receiving_litellm_response(
                temperature=LITELLM_TEMPERATURE,
                messages=messages,
                user=context.user_id,
            )
            if user_id is None:
                raise ValueError("user_id cannot be None")
            consume_litellm_stream_to_write_reply(
                client=client,
                wip_reply=wip_reply,
                context=context,
                user_id=user_id,
                messages=messages,
                stream=stream,
                thread_ts=payload["ts"],
                loading_text=loading_text,
                timeout_seconds=LITELLM_TIMEOUT_SECONDS,
                translate_markdown=TRANSLATE_MARKDOWN,
                logger=context.logger,
            )

    except (Timeout, TimeoutError) as e:
        if wip_reply is not None:
            message_dict: dict = wip_reply.get("message", {})
            text = (
                (message_dict.get("text", "") if wip_reply is not None else "")
                + "\n\n"
                + translate(
                    locale=context.get("locale"),
                    text=TIMEOUT_ERROR_MESSAGE,
                )
            )
            if context.channel_id is None:
                raise ValueError("context.channel_id cannot be None") from e
            client.chat_update(
                channel=context.channel_id,
                ts=wip_reply["message"]["ts"],
                text=text,
            )
    except Exception as e:
        message_dict = wip_reply.get("message", {}) if wip_reply is not None else {}
        text = (
            message_dict.get("text", "")
            + "\n\n"
            + translate(
                locale=context.get("locale"),
                text=f":warning: Failed to start a conversation with AI: {e}",
            )
        )
        logger.exception(text)
        if wip_reply is not None:
            if context.channel_id is None:
                raise ValueError("context.channel_id cannot be None") from e
            client.chat_update(
                channel=context.channel_id,
                ts=wip_reply["message"]["ts"],
                text=text,
            )


def respond_to_new_message(
    context: BoltContext,
    payload: dict,
    client: WebClient,
    logger: logging.Logger,
):
    if payload.get("bot_id") is not None and payload.get("bot_id") != context.bot_id:
        # Skip a new message by a different app
        return

    wip_reply = None
    try:
        is_in_dm_with_bot = payload.get("channel_type") == "im"
        is_thread_for_this_app = False
        thread_ts = payload.get("thread_ts")
        if not is_in_dm_with_bot and thread_ts is None:
            return

        if context.channel_id is None:
            raise ValueError("context.channel_id cannot be None")
        messages_in_context = []
        # In the DM with the bot; this is not within a thread
        if is_in_dm_with_bot and thread_ts is None:
            past_messages: list[dict] = client.conversations_history(
                channel=context.channel_id,
                include_all_metadata=True,
                limit=100,
            ).get("messages", [])
            past_messages.reverse()
            # Remove old messages
            for message in past_messages:
                ts: Optional[str] = message.get("ts")
                if ts is None:
                    logger.warning("The message does not have a timestamp")
                    continue
                seconds = time.time() - float(ts)
                if seconds < 86400:  # less than 1 day
                    messages_in_context.append(message)
            is_thread_for_this_app = True
        # Within a thread
        else:
            if thread_ts is None:
                raise ValueError("thread_ts cannot be None")
            messages_in_context = client.conversations_replies(
                channel=context.channel_id,
                ts=thread_ts,
                include_all_metadata=True,
                limit=1000,
            ).get("messages", [])
            if is_in_dm_with_bot:
                # In the DM with this bot
                is_thread_for_this_app = True
            else:
                # In a channel
                the_parent_message_found = False
                for message in messages_in_context:
                    if message.get("ts") == thread_ts:
                        the_parent_message_found = True
                        is_thread_for_this_app = is_this_app_mentioned(
                            context.bot_user_id, message
                        )
                        break
                if the_parent_message_found is False:
                    parent_message = find_parent_message(
                        client, context.channel_id, thread_ts
                    )
                    if parent_message is not None:
                        is_thread_for_this_app = is_this_app_mentioned(
                            context.bot_user_id, parent_message
                        )

        if is_thread_for_this_app is False:
            return

        messages: list[dict] = []
        user_id = context.actor_user_id or context.user_id
        last_assistant_idx = -1
        indices_to_remove = []
        for idx, reply in enumerate(messages_in_context):
            maybe_event_type = reply.get("metadata", {}).get("event_type")
            if maybe_event_type == "litellm":
                if context.bot_id != reply.get("bot_id"):
                    # Remove messages by a different app
                    indices_to_remove.append(idx)
                    continue
                maybe_new_messages = (
                    reply.get("metadata", {}).get("event_payload", {}).get("messages")
                )
                if maybe_new_messages is not None:
                    if len(messages) == 0 or user_id is None:
                        new_user_id = (
                            reply.get("metadata", {})
                            .get("event_payload", {})
                            .get("user")
                        )
                        if new_user_id is not None:
                            user_id = new_user_id
                    messages = maybe_new_messages
                    last_assistant_idx = idx

        # To know whether this app needs to start a new convo
        if (is_in_dm_with_bot or last_assistant_idx == -1) and not next(
            filter(lambda msg: msg["role"] == "system", messages), None
        ):
            # Replace placeholder for Slack user ID in the system prompt
            system_text = build_system_text(
                SYSTEM_TEXT, TRANSLATE_MARKDOWN, context.bot_user_id
            )
            messages.insert(0, {"role": "system", "content": system_text})

        filtered_messages_in_context = []
        for idx, reply in enumerate(messages_in_context):
            # Strip bot Slack user ID from initial message
            if idx == 0:
                reply["text"] = re.sub(
                    f"<@{context.bot_user_id}>\\s*", "", reply["text"]
                )
            if idx not in indices_to_remove:
                filtered_messages_in_context.append(reply)
        if not filtered_messages_in_context:
            return

        for reply in filtered_messages_in_context:
            msg_user_id = reply.get("user")
            reply_text = redact_string(reply.get("text") or "")
            content = [
                {
                    "type": "text",
                    "text": f"<@{msg_user_id}>: "
                    + format_litellm_message_content(reply_text, TRANSLATE_MARKDOWN),
                }
            ]
            if (
                reply.get("bot_id") is None
                and context.authorize_result is not None
                and can_send_image_url_to_litellm(context.authorize_result.bot_scopes)
            ):
                if context.bot_token is None:
                    raise ValueError("context.bot_token cannot be None")
                content += get_image_content_if_exists(
                    bot_token=context.bot_token,
                    files=reply.get("files"),
                    logger=context.logger,
                )
            if (
                reply.get("bot_id") is None
                and context.authorize_result is not None
                and can_send_pdf_url_to_litellm(context.authorize_result.bot_scopes)
            ):
                if context.bot_token is None:
                    raise ValueError("context.bot_token cannot be None")
                content += get_pdf_content_if_exists(
                    bot_token=context.bot_token,
                    files=reply.get("files"),
                    logger=context.logger,
                )

            role = (
                "assistant"
                if "user" in reply and reply["user"] == context.bot_user_id
                else "user"
            )
            messages.append(
                {
                    "content": (content if role == "user" else content[0]["text"]),
                    "role": role,
                }
            )

        loading_text = translate(
            locale=context.get("locale"), text=DEFAULT_LOADING_TEXT
        )
        if context.channel_id is None:
            raise ValueError("context.channel_id cannot be None")
        if user_id is None:
            raise ValueError("user_id cannot be None")
        thread_ts = payload.get("thread_ts") if is_in_dm_with_bot else payload["ts"]
        wip_reply = post_wip_message(
            client=client,
            channel=context.channel_id,
            thread_ts=thread_ts,
            loading_text=loading_text,
            messages=messages,
            user=user_id,
        )

        trim_pdf_content(messages)
        (
            messages,
            num_context_tokens,
            max_context_tokens,
        ) = messages_within_context_window(messages)
        num_messages = len([msg for msg in messages if msg.get("role") != "system"])
        if num_messages == 0:
            if context.channel_id is None:
                raise ValueError("context.channel_id cannot be None")
            if context.user_id is None:
                raise ValueError("context.user_id cannot be None")
            update_wip_message(
                client=client,
                channel=context.channel_id,
                ts=wip_reply["message"]["ts"],
                text=(
                    f":warning: The previous message is too long "
                    f"({num_context_tokens}/{max_context_tokens} prompt tokens)."
                ),
                messages=messages,
                user=context.user_id,
            )
        else:
            stream = start_receiving_litellm_response(
                temperature=LITELLM_TEMPERATURE,
                messages=messages,
                user=user_id,
            )

            if context.channel_id is None:
                raise ValueError("context.channel_id cannot be None")
            ts = wip_reply.get("ts")
            if ts is None:
                raise ValueError("ts cannot be None")
            latest_replies = client.conversations_replies(
                channel=context.channel_id,
                ts=ts,
                include_all_metadata=True,
                limit=1000,
            )
            latest_replies_messages: list[dict] = latest_replies.get("messages", [])
            if not latest_replies_messages:
                return
            if latest_replies_messages[-1]["ts"] != wip_reply["message"]["ts"]:
                # Since a new reply will come soon, this app abandons this reply
                client.chat_delete(
                    channel=context.channel_id,
                    ts=wip_reply["message"]["ts"],
                )
                return

            consume_litellm_stream_to_write_reply(
                client=client,
                wip_reply=wip_reply,
                context=context,
                user_id=user_id,
                messages=messages,
                stream=stream,
                thread_ts=thread_ts,
                loading_text=loading_text,
                timeout_seconds=LITELLM_TIMEOUT_SECONDS,
                translate_markdown=TRANSLATE_MARKDOWN,
                logger=context.logger,
            )

    except (Timeout, TimeoutError) as e:
        if wip_reply is not None:
            message_dict: dict = wip_reply.get("message", {})
            text = (
                (message_dict.get("text", "") if wip_reply is not None else "")
                + "\n\n"
                + translate(
                    locale=context.get("locale"),
                    text=TIMEOUT_ERROR_MESSAGE,
                )
            )
            if context.channel_id is None:
                raise ValueError("context.channel_id cannot be None") from e
            client.chat_update(
                channel=context.channel_id,
                ts=wip_reply["message"]["ts"],
                text=text,
            )
    except Exception as e:
        message_dict = wip_reply.get("message", {}) if wip_reply is not None else {}
        text = message_dict.get("text", "") + "\n\n" + f":warning: Failed to reply: {e}"
        logger.exception(text)
        if wip_reply is not None:
            if context.channel_id is None:
                raise ValueError("context.channel_id cannot be None") from e
            client.chat_update(
                channel=context.channel_id,
                ts=wip_reply["message"]["ts"],
                text=text,
            )


def register_listeners(app: App):
    # TODO: remove this workaround once bolt-python attaches scopes to context under the hood
    app.middleware(attach_bot_scopes)

    # Chat with the bot
    app.event("app_mention")(ack=just_ack, lazy=[respond_to_app_mention])
    app.event("message")(ack=just_ack, lazy=[respond_to_new_message])


MESSAGE_SUBTYPES_TO_SKIP = ["message_changed", "message_deleted"]


# To reduce unnecessary workload in this app,
# this before_authorize function skips message changed/deleted events.
# Especially, "message_changed" events can be triggered many times when the app rapidly updates its reply.
def before_authorize(
    body: dict,
    payload: dict,
    logger: logging.Logger,
    next_,
):
    if (
        is_event(body)
        and payload.get("type") == "message"
        and payload.get("subtype") in MESSAGE_SUBTYPES_TO_SKIP
    ):
        logger.debug(
            "Skipped the following middleware and listeners "
            f"for this message event (subtype: {payload.get('subtype')})"
        )
        return BoltResponse(status=200, body="")
    next_()
