import json
import logging
import os
import threading
import time
from functools import lru_cache
from importlib import import_module
from types import ModuleType
from typing import Optional, Tuple, Union

import litellm
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from litellm.types.utils import (
    ChatCompletionMessageToolCall,
    Choices,
    Message,
    ModelResponse,
)
from slack_sdk.web import SlackResponse, WebClient

from app.env import (
    LITELLM_CALLBACK_MODULE_NAME,
    LITELLM_MAX_TOKENS,
    LITELLM_MODEL,
    LITELLM_MODEL_TYPE,
    LITELLM_TEMPERATURE,
    LITELLM_TOOLS_MODULE_NAME,
    SLACK_LOADING_CHARACTER,
    SLACK_UPDATE_TEXT_BUFFER_SIZE,
    TRANSLATE_MARKDOWN,
)
from app.exceptions import ContextOverflowError
from app.litellm_logic import get_max_input_tokens
from app.message_logic import (
    convert_markdown_to_mrkdwn,
    format_assistant_reply_for_slack,
)

litellm.drop_params = True

if LITELLM_CALLBACK_MODULE_NAME is not None:
    callback_module = import_module(LITELLM_CALLBACK_MODULE_NAME)
    litellm.callbacks = [callback_module.CallbackHandler()]


# Remove old messages to make sure we have room for max_input_tokens
def trim_messages_to_fit_context(
    messages: list[dict],
) -> Tuple[int, int]:
    max_input_tokens = get_max_input_tokens(LITELLM_MODEL_TYPE)
    if max_input_tokens is None:
        raise ValueError("LiteLLM does not support the model type")

    tools_tokens = 0
    if LITELLM_TOOLS_MODULE_NAME is not None:
        tools_tokens = calculate_tokens_necessary_for_tools()

    max_context_tokens = max_input_tokens - tools_tokens - LITELLM_MAX_TOKENS - 1

    while True:
        messages_tokens = litellm.utils.token_counter(
            model=LITELLM_MODEL_TYPE, messages=messages
        )
        if messages_tokens <= max_context_tokens:
            break
        if len(messages) == 2:
            raise ContextOverflowError(messages_tokens, max_context_tokens)
        for i, message in enumerate(messages):
            if message["role"] in ("user", "assistant", "function"):
                del messages[i]
                break
        else:
            # Fall through and let the LiteLLM error handler deal with it
            break

    return messages_tokens, tools_tokens


def reply_to_slack_with_litellm(
    *,
    client: WebClient,
    channel: str,
    user_id: str,
    thread_ts: Optional[str],
    messages: list[dict],
    loading_text: str,
    wip_reply: Union[dict, SlackResponse],
    timeout_seconds: int,
) -> None:
    stream = start_receiving_litellm_response(
        temperature=LITELLM_TEMPERATURE,
        messages=messages,
        user=user_id,
    )
    consume_litellm_stream_to_write_reply(
        client=client,
        wip_reply=wip_reply,
        channel=channel,
        user_id=user_id,
        messages=messages,
        stream=stream,
        thread_ts=thread_ts,
        loading_text=loading_text,
        timeout_seconds=timeout_seconds,
    )


@lru_cache(maxsize=1)
def calculate_tokens_necessary_for_tools() -> int:
    """Calculates the estimated number of prompt tokens necessary for loading Tools stuff"""
    if LITELLM_TOOLS_MODULE_NAME is None:
        return 0

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
    module = import_module(LITELLM_TOOLS_MODULE_NAME)
    return _calculate_prompt_tokens(module.tools) - _calculate_prompt_tokens(None)


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


def consume_litellm_stream_to_write_reply(
    *,
    client: WebClient,
    wip_reply: Union[dict, SlackResponse],
    channel: str,
    user_id: str,
    messages: list[dict],
    stream: CustomStreamWrapper,
    thread_ts: Optional[str],
    loading_text: str,
    timeout_seconds: int,
):
    start_time = time.time()
    assistant_reply = {
        "role": "assistant",
        "content": "",
    }

    response_message, is_response_too_long = handle_litellm_stream(
        stream=stream,
        assistant_reply=assistant_reply,
        wip_reply=wip_reply,
        client=client,
        channel=channel,
        timeout_seconds=timeout_seconds,
        start_time=start_time,
    )

    # Append any remaining text to the message
    if len(assistant_reply["content"]) > 0:
        update_reply_text(
            client=client,
            channel=channel,
            wip_reply=wip_reply,
            assistant_content=assistant_reply["content"],
            with_loading_character=False,
        )

    messages.append(assistant_reply)

    # If the response is too long, post a new message instead
    if is_response_too_long:
        next_wip_reply = client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=SLACK_LOADING_CHARACTER,
        )
        consume_litellm_stream_to_write_reply(
            client=client,
            wip_reply=next_wip_reply,
            channel=channel,
            user_id=user_id,
            messages=messages,
            stream=stream,
            thread_ts=thread_ts,
            loading_text=loading_text,
            timeout_seconds=int(timeout_seconds - (time.time() - start_time)),
        )

    if (
        response_message is None
        or response_message.tool_calls is None
        or LITELLM_TOOLS_MODULE_NAME is None
    ):
        return

    # If the message has already been updated, post a new one
    if wip_reply["message"]["text"] != loading_text:
        wip_reply = client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=loading_text,
        )

    process_tool_calls(
        response_message=response_message,
        tools_module_name=LITELLM_TOOLS_MODULE_NAME,
        assistant_reply=assistant_reply,
        messages=messages,
        logger=client.logger,
    )
    trim_messages_to_fit_context(messages)
    reply_to_slack_with_litellm(
        client=client,
        wip_reply=wip_reply,
        channel=channel,
        user_id=user_id,
        messages=messages,
        thread_ts=thread_ts,
        loading_text=loading_text,
        timeout_seconds=int(timeout_seconds - (time.time() - start_time)),
    )


def handle_litellm_stream(
    *,
    stream: CustomStreamWrapper,
    assistant_reply: dict,
    wip_reply: Union[dict, SlackResponse],
    client: WebClient,
    channel: str,
    timeout_seconds: int,
    start_time: float,
) -> tuple[Optional[Message], bool]:
    response_chunks: list = []
    is_response_too_long = False
    threads: list[threading.Thread] = []
    buffered_text = ""
    try:
        for chunk in stream:
            if (time.time() - start_time) > timeout_seconds:
                raise TimeoutError()
            response_chunks.append(chunk)
            delta = chunk.choices[0].get("delta")
            if delta is None or delta.get("content") is None:
                continue
            buffered_text += delta["content"]
            assistant_reply["content"] += delta["content"]
            is_final_chunk = chunk.choices[0].get("finish_reason") is not None
            if len(buffered_text) >= SLACK_UPDATE_TEXT_BUFFER_SIZE:
                spawn_reply_update_text(
                    client=client,
                    channel=channel,
                    wip_reply=wip_reply,
                    assistant_content=assistant_reply["content"],
                    threads=threads,
                )
                buffered_text = ""
                if (
                    not is_final_chunk
                    and len(wip_reply["message"]["text"].encode("utf-8")) > 3500
                ):
                    is_response_too_long = True
                    break
            if is_final_chunk:
                break
    finally:
        for t in threads:
            try:
                t.join()
            except Exception:
                pass
    return build_litellm_response(response_chunks), is_response_too_long


def update_reply_text(
    client: WebClient,
    channel: str,
    wip_reply: Union[dict, SlackResponse],
    assistant_content: str,
    with_loading_character: bool = True,
) -> None:
    assistant_reply_text = format_assistant_reply_for_slack(assistant_content)
    if TRANSLATE_MARKDOWN:
        assistant_reply_text = convert_markdown_to_mrkdwn(assistant_reply_text)
    wip_reply["message"]["text"] = assistant_reply_text
    text = assistant_reply_text
    if with_loading_character:
        text += SLACK_LOADING_CHARACTER
    client.chat_update(
        channel=channel,
        ts=wip_reply["message"]["ts"],
        text=text,
    )


def spawn_reply_update_text(
    *,
    client: WebClient,
    channel: str,
    wip_reply: Union[dict, SlackResponse],
    assistant_content: str,
    threads: list[threading.Thread],
) -> None:
    thread = threading.Thread(
        target=update_reply_text,
        args=(client, channel, wip_reply, assistant_content),
    )
    thread.daemon = True
    thread.start()
    threads.append(thread)


def build_litellm_response(chunks: list) -> Optional[Message]:
    response = litellm.stream_chunk_builder(chunks)
    if response is None:
        raise RuntimeError(
            "litellm.stream_chunk_builder returned None. "
            "Check the stream data or API behavior."
        )
    if isinstance(response.choices[0], Choices):
        return response.choices[0].message
    return None


def process_tool_calls(
    *,
    response_message: Message,
    tools_module_name: str,
    assistant_reply: dict,
    messages: list[dict],
    logger: logging.Logger,
) -> None:
    if response_message.tool_calls is None:
        return
    assistant_reply["tool_calls"] = response_message.model_dump()["tool_calls"]
    tools_module = import_module(tools_module_name)
    for tool_call in response_message.tool_calls:
        process_tool_call(tool_call, tools_module, messages, logger)


def process_tool_call(
    tool_call: ChatCompletionMessageToolCall,
    tools_module: ModuleType,
    messages: list[dict],
    logger: logging.Logger,
) -> None:
    function_name = tool_call.function.name
    if function_name is None:
        logger.warning(
            "Skipped a tool call due to missing function name. Tool call details: %s",
            tool_call,
        )
        return
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
