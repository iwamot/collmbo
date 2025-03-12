import json
import logging
import os
import re
import threading
import time
from importlib import import_module
from typing import Optional, Tuple, Union

import litellm
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from litellm.types.utils import ModelResponse
from slack_bolt import BoltContext
from slack_sdk.web import SlackResponse, WebClient

from app.env import (
    LITELLM_CALLBACK_MODULE_NAME,
    LITELLM_MAX_TOKENS,
    LITELLM_MODEL,
    LITELLM_MODEL_TYPE,
    LITELLM_TEMPERATURE,
    LITELLM_TOOLS_MODULE_NAME,
    SLACK_UPDATE_TEXT_BUFFER_SIZE,
)
from app.markdown_conversion import markdown_to_slack, slack_to_markdown
from app.slack_api_ops import post_wip_message, update_wip_message

# ----------------------------
# Internal functions
# ----------------------------

litellm.drop_params = True

if LITELLM_CALLBACK_MODULE_NAME is not None:
    callback_module = import_module(LITELLM_CALLBACK_MODULE_NAME)
    litellm.callbacks = [callback_module.CallbackHandler()]

_prompt_tokens_used_by_tools_cache: Optional[int] = None


# Format message from Slack to send to LiteLLM
def format_litellm_message_content(content: str, translate_markdown: bool) -> str:
    # Unescape &, < and >, since Slack replaces these with their HTML equivalents
    # See also: https://api.slack.com/reference/surfaces/formatting#escaping
    content = content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

    # Convert from Slack mrkdwn to Markdown format
    if translate_markdown:
        content = slack_to_markdown(content)

    return content


# Remove old messages to make sure we have room for max_input_tokens
def messages_within_context_window(
    messages: list[dict],
) -> Tuple[list[dict], int, int]:
    model_info = litellm.utils.get_model_info(LITELLM_MODEL_TYPE)
    max_input_tokens = model_info.get("max_input_tokens") or model_info.get(
        "max_tokens"
    )
    if max_input_tokens is None:
        raise ValueError("LiteLLM does not support the model type")
    max_context_tokens = max_input_tokens - LITELLM_MAX_TOKENS - 1
    if LITELLM_TOOLS_MODULE_NAME is not None:
        max_context_tokens -= calculate_tokens_necessary_for_tools()
    num_context_tokens = 0  # Number of tokens in the context window just before the earliest message is deleted
    while (
        num_tokens := litellm.utils.token_counter(
            model=LITELLM_MODEL_TYPE, messages=messages
        )
    ) > max_context_tokens:
        removed = False
        for i, message in enumerate(messages):
            if message["role"] in ("user", "assistant", "function"):
                num_context_tokens = num_tokens
                del messages[i]
                removed = True
                break
        if not removed:
            # Fall through and let the LiteLLM error handler deal with it
            break
    else:
        num_context_tokens = num_tokens

    # Remove any non-user messages at the beginning of the list
    while messages and messages[0]["role"] != "user":
        num_context_tokens = litellm.utils.token_counter(
            model=LITELLM_MODEL_TYPE, messages=messages
        )
        del messages[0]

    # Remove any assistant messages at the end of the list
    while messages and messages[-1]["role"] == "assistant":
        num_context_tokens = litellm.utils.token_counter(
            model=LITELLM_MODEL_TYPE, messages=messages
        )
        del messages[-1]

    return messages, num_context_tokens, max_context_tokens


def start_receiving_litellm_response(
    *,
    temperature: float,
    messages: list[dict],
    user: str,
) -> CustomStreamWrapper:
    if LITELLM_TOOLS_MODULE_NAME is not None:
        tools = import_module(LITELLM_TOOLS_MODULE_NAME).tools
    else:
        tools = None
    response = call_litellm_completion(
        messages=messages,
        max_tokens=LITELLM_MAX_TOKENS,
        temperature=temperature,
        user=user,
        stream=True,
        tools=tools,
    )
    if not isinstance(response, CustomStreamWrapper):
        raise TypeError("Expected CustomStreamWrapper when streaming is enabled")
    return response


def call_litellm_completion(
    *,
    messages: list[dict],
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0,
    stream: bool = False,
    tools: Optional[list] = None,
) -> Union[ModelResponse, CustomStreamWrapper]:
    return litellm.completion(
        model=LITELLM_MODEL,
        messages=messages,
        top_p=1,
        n=1,
        max_tokens=max_tokens,
        temperature=temperature,
        presence_penalty=0,
        frequency_penalty=0,
        user=user,
        stream=stream,
        tools=tools,
        aws_region_name=os.environ.get("AWS_REGION_NAME"),
    )


def consume_litellm_stream_to_write_reply(
    *,
    client: WebClient,
    wip_reply: Union[dict, SlackResponse],
    context: BoltContext,
    user_id: str,
    messages: list[dict],
    stream: CustomStreamWrapper,
    thread_ts: Optional[str],
    loading_text: str,
    timeout_seconds: int,
    translate_markdown: bool,
    logger: logging.Logger,
):
    if context.channel_id is None:
        raise ValueError("context.channel_id cannot be None")

    start_time = time.time()
    assistant_reply = {
        "role": "assistant",
        "content": "",
    }
    messages.append(assistant_reply)
    pending_text = ""
    threads = []
    chunks: list = []
    is_response_too_long = False
    try:
        loading_character = " ... :writing_hand:"
        for chunk in stream:
            spent_seconds = time.time() - start_time
            if timeout_seconds < spent_seconds:
                raise TimeoutError()
            chunks.append(chunk)
            item = chunk.choices[0]
            if item.get("finish_reason") is not None:
                break
            delta = item.get("delta")
            if delta is not None and delta.get("content") is not None:
                pending_text += delta.get("content")
                assistant_reply["content"] += delta.get("content")
                if len(pending_text) >= SLACK_UPDATE_TEXT_BUFFER_SIZE:

                    def update_message():
                        assistant_reply_text = format_assistant_reply(
                            assistant_reply["content"], translate_markdown
                        )
                        wip_reply["message"]["text"] = assistant_reply_text
                        update_wip_message(
                            client=client,
                            channel=context.channel_id,
                            ts=wip_reply["message"]["ts"],
                            text=assistant_reply_text + loading_character,
                            messages=messages,
                            user=user_id,
                        )

                    thread = threading.Thread(target=update_message)
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                    pending_text = ""

                    if len(wip_reply["message"]["text"].encode("utf-8")) > 3500:
                        is_response_too_long = True
                        break

        for t in threads:
            try:
                if t.is_alive():
                    t.join()
            except Exception:
                pass

        # Append any remaining text to the message
        if len(assistant_reply["content"]) > 0:
            assistant_reply_text = format_assistant_reply(
                assistant_reply["content"], translate_markdown
            )
            wip_reply["message"]["text"] = assistant_reply_text
            update_wip_message(
                client=client,
                channel=context.channel_id,
                ts=wip_reply["message"]["ts"],
                text=assistant_reply_text,
                messages=messages,
                user=user_id,
            )

        # If the response is too long, post a new message instead
        if is_response_too_long:
            next_wip_reply = post_wip_message(
                client=client,
                channel=context.channel_id,
                thread_ts=thread_ts,
                loading_text=loading_character,
                messages=messages,
                user=user_id,
            )
            consume_litellm_stream_to_write_reply(
                client=client,
                wip_reply=next_wip_reply,
                context=context,
                user_id=user_id,
                messages=messages,
                stream=stream,
                thread_ts=thread_ts,
                loading_text=loading_text,
                timeout_seconds=int(timeout_seconds - (time.time() - start_time)),
                translate_markdown=translate_markdown,
                logger=logger,
            )

        response = litellm.stream_chunk_builder(chunks)
        if response is None:
            raise RuntimeError(
                "Unexpected None response from 'litellm.stream_chunk_builder'. "
                "Check the input 'chunks' and the Litellm API behavior."
            )
        response_message = response.choices[0].get("message")
        if (
            response_message is not None
            and response_message.tool_calls is not None
            and LITELLM_TOOLS_MODULE_NAME is not None
        ):
            # If the message has already been updated, post a new one
            if wip_reply["message"]["text"] != loading_text:
                wip_reply = post_wip_message(
                    client=client,
                    channel=context.channel_id,
                    thread_ts=thread_ts,
                    loading_text=loading_text,
                    messages=messages,
                    user=user_id,
                )

            tool_calls = response_message.tool_calls
            assistant_reply["tool_calls"] = response_message.model_dump()["tool_calls"]
            tools_module = import_module(LITELLM_TOOLS_MODULE_NAME)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                if function_name is None:
                    logger.warning(
                        "Skipped a tool call due to missing function name. Tool call details: %s",
                        tool_call,
                    )
                    continue
                function_to_call = getattr(tools_module, function_name)
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
            messages_within_context_window(messages)
            sub_stream = start_receiving_litellm_response(
                temperature=LITELLM_TEMPERATURE,
                messages=messages,
                user=user_id,
            )
            consume_litellm_stream_to_write_reply(
                client=client,
                wip_reply=wip_reply,
                context=context,
                user_id=user_id,
                messages=messages,
                stream=sub_stream,
                thread_ts=thread_ts,
                loading_text=loading_text,
                timeout_seconds=int(timeout_seconds - (time.time() - start_time)),
                translate_markdown=translate_markdown,
                logger=logger,
            )

    finally:
        for t in threads:
            try:
                if t.is_alive():
                    t.join()
            except Exception:
                pass


# Format message from LiteLLM to display in Slack
def format_assistant_reply(content: str, translate_markdown: bool) -> str:
    for o, n in [
        # Remove leading newlines
        ("^\n+", ""),
        # Remove prepended Slack user ID
        ("^<@U.*?>\\s?:\\s?", ""),
        # Remove code block tags since Slack doesn't render them in a message
        ("```\\s*[Rr]ust\n", "```\n"),
        ("```\\s*[Rr]uby\n", "```\n"),
        ("```\\s*[Ss]cala\n", "```\n"),
        ("```\\s*[Kk]otlin\n", "```\n"),
        ("```\\s*[Jj]ava\n", "```\n"),
        ("```\\s*[Gg]o\n", "```\n"),
        ("```\\s*[Ss]wift\n", "```\n"),
        ("```\\s*[Oo]objective[Cc]\n", "```\n"),
        ("```\\s*[Cc]\n", "```\n"),
        ("```\\s*[Cc][+][+]\n", "```\n"),
        ("```\\s*[Cc][Pp][Pp]\n", "```\n"),
        ("```\\s*[Cc]sharp\n", "```\n"),
        ("```\\s*[Mm][Aa][Tt][Ll][Aa][Bb]\n", "```\n"),
        ("```\\s*[Jj][Ss][Oo][Nn]\n", "```\n"),
        ("```\\s*[Ll]a[Tt]e[Xx]\n", "```\n"),
        ("```\\s*[Ll][Uu][Aa]\n", "```\n"),
        ("```\\s*[Cc][Mm][Aa][Kk][Ee]\n", "```\n"),
        ("```\\s*bash\n", "```\n"),
        ("```\\s*zsh\n", "```\n"),
        ("```\\s*sh\n", "```\n"),
        ("```\\s*[Ss][Qq][Ll]\n", "```\n"),
        ("```\\s*[Pp][Hh][Pp]\n", "```\n"),
        ("```\\s*[Pp][Ee][Rr][Ll]\n", "```\n"),
        ("```\\s*[Jj]ava[Ss]cript\n", "```\n"),
        ("```\\s*[Ty]ype[Ss]cript\n", "```\n"),
        ("```\\s*[Pp]ython\n", "```\n"),
    ]:
        content = re.sub(o, n, content)

    # Convert from Markdown to Slack mrkdwn format
    if translate_markdown:
        content = markdown_to_slack(content)

    return content


def build_system_text(
    system_text_template: str, translate_markdown: bool, bot_user_id: Optional[str]
):
    system_text = system_text_template.format(bot_user_id=bot_user_id)
    # Translate format hint in system prompt
    if translate_markdown:
        system_text = slack_to_markdown(system_text)
    return system_text


def calculate_tokens_necessary_for_tools() -> int:
    """Calculates the estimated number of prompt tokens necessary for loading Tools stuff"""
    tools_module_name = LITELLM_TOOLS_MODULE_NAME
    if tools_module_name is None:
        return 0

    global _prompt_tokens_used_by_tools_cache
    if _prompt_tokens_used_by_tools_cache is not None:
        return _prompt_tokens_used_by_tools_cache

    def _calculate_prompt_tokens(tools) -> int:
        response = call_litellm_completion(
            messages=[{"role": "user", "content": "hello"}],
            user="system",
            tools=tools,
        )
        if not isinstance(response, ModelResponse):
            raise TypeError("Expected ModelResponse when streaming is disabled")
        return response["usage"]["prompt_tokens"]

    # TODO: If there is a better way to calculate this, replace the logic with it
    module = import_module(tools_module_name)
    _prompt_tokens_used_by_tools_cache = _calculate_prompt_tokens(
        module.tools
    ) - _calculate_prompt_tokens(None)
    return _prompt_tokens_used_by_tools_cache
