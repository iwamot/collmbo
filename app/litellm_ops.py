import json
import os
import re
import threading
import time
from importlib import import_module
from typing import Dict, List, Optional, Tuple, Union

import litellm
from slack_bolt import BoltContext
from slack_sdk.web import SlackResponse, WebClient

from app.env import (
    LITELLM_CALLBACK_MODULE_NAME,
    LITELLM_MAX_TOKENS,
    LITELLM_MODEL,
    LITELLM_MODEL_TYPE,
    LITELLM_TEMPERATURE,
    LITELLM_TOOLS_MODULE_NAME,
)
from app.markdown_conversion import markdown_to_slack, slack_to_markdown
from app.slack_ops import update_wip_message

# ----------------------------
# Internal functions
# ----------------------------

litellm.drop_params = True

if LITELLM_CALLBACK_MODULE_NAME is not None:
    callback_module = import_module(LITELLM_CALLBACK_MODULE_NAME)
    litellm.callbacks = [callback_module.CallbackHandler()]

_prompt_tokens_used_by_tools_cache: Optional[int] = None


# Format message from Slack to send to LiteLLM
def format_litellm_message_content(
    content: str, translate_markdown: bool
) -> Optional[str]:
    if content is None:
        return None

    # Unescape &, < and >, since Slack replaces these with their HTML equivalents
    # See also: https://api.slack.com/reference/surfaces/formatting#escaping
    content = content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

    # Convert from Slack mrkdwn to Markdown format
    if translate_markdown:
        content = slack_to_markdown(content)

    return content


# Remove old messages to make sure we have room for max_tokens
def messages_within_context_window(
    messages: List[Dict[str, Union[str, Dict[str, str]]]],
) -> Tuple[List[Dict[str, Union[str, Dict[str, str]]]], int, int]:
    max_context_tokens = (
        litellm.get_max_tokens(LITELLM_MODEL_TYPE) - LITELLM_MAX_TOKENS - 1
    )
    if LITELLM_TOOLS_MODULE_NAME is not None:
        max_context_tokens -= calculate_tokens_necessary_for_tools()
    num_context_tokens = 0  # Number of tokens in the context window just before the earliest message is deleted
    while (
        num_tokens := litellm.token_counter(model=LITELLM_MODEL_TYPE, messages=messages)
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

    return messages, num_context_tokens, max_context_tokens


def start_receiving_litellm_response(
    *,
    temperature: float,
    messages: List[Dict[str, Union[str, Dict[str, str]]]],
    user: str,
) -> Union[litellm.ModelResponse, litellm.CustomStreamWrapper]:
    if LITELLM_TOOLS_MODULE_NAME is not None:
        tools = import_module(LITELLM_TOOLS_MODULE_NAME).tools
    else:
        tools = None
    return call_litellm_completion(
        messages=messages,
        max_tokens=LITELLM_MAX_TOKENS,
        temperature=temperature,
        user=user,
        stream=True,
        tools=tools,
    )


def call_litellm_completion(
    *,
    messages: List[Dict[str, Union[str, Dict[str, str]]]],
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0,
    stream: bool = False,
    tools: Optional[List] = None,
) -> Union[litellm.ModelResponse, litellm.CustomStreamWrapper]:
    return litellm.completion(
        model=LITELLM_MODEL,
        messages=messages,
        top_p=1,
        n=1,
        max_tokens=max_tokens,
        temperature=temperature,
        presence_penalty=0,
        frequency_penalty=0,
        logit_bias={},
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
    messages: List[Dict[str, Union[str, Dict[str, str], List]]],
    stream: Union[litellm.ModelResponse, litellm.CustomStreamWrapper],
    timeout_seconds: int,
    translate_markdown: bool,
):
    start_time = time.time()
    assistant_reply: Dict[str, Union[str, Dict[str, str], List]] = {
        "role": "assistant",
        "content": "",
    }
    messages.append(assistant_reply)
    word_count = 0
    threads = []
    tool_calls = []
    try:
        loading_character = " ... :writing_hand:"
        for chunk in stream:
            spent_seconds = time.time() - start_time
            if timeout_seconds < spent_seconds:
                raise TimeoutError()
            item = chunk.choices[0]
            if item.get("finish_reason") is not None:
                break
            delta = item.get("delta")
            if delta.get("content") is not None:
                word_count += 1
                assistant_reply["content"] += delta.get("content")
                if word_count >= 20:

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
                    word_count = 0
            if delta.get("tool_calls") is not None:
                tool_call = delta.get("tool_calls")[0]
                if len(tool_calls) <= tool_call.index:
                    tool_calls.append(
                        {
                            "id": tool_call.id,
                            "function": {
                                "name": "",
                                "arguments": "",
                            },
                            "type": tool_call.type,
                        }
                    )
                function = tool_calls[tool_call.index]["function"]
                function["name"] += tool_call.function.name or ""
                function["arguments"] += tool_call.function.arguments or ""

        for t in threads:
            try:
                if t.is_alive():
                    t.join()
            except Exception:
                pass

        if len(tool_calls) > 0:
            assistant_reply["tool_calls"] = tool_calls
            tools_module = import_module(LITELLM_TOOLS_MODULE_NAME)
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_to_call = getattr(tools_module, function_name)
                function_args = json.loads(tool_call["function"]["arguments"])
                function_response = function_to_call(**function_args)
                messages.append(
                    {
                        "tool_call_id": tool_call["id"],
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
                timeout_seconds=int(timeout_seconds - (time.time() - start_time)),
                translate_markdown=translate_markdown,
            )
            return

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
    finally:
        for t in threads:
            try:
                if t.is_alive():
                    t.join()
            except Exception:
                pass
        try:
            stream.close()
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
    system_text_template: str, translate_markdown: bool, context: BoltContext
):
    system_text = system_text_template.format(bot_user_id=context.bot_user_id)
    # Translate format hint in system prompt
    if translate_markdown is True:
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
        return call_litellm_completion(
            messages=[{"role": "user", "content": "hello"}],
            user="system",
            tools=tools,
        )["usage"]["prompt_tokens"]

    # TODO: If there is a better way to calculate this, replace the logic with it
    module = import_module(tools_module_name)
    _prompt_tokens_used_by_tools_cache = _calculate_prompt_tokens(
        module.tools
    ) - _calculate_prompt_tokens(None)
    return _prompt_tokens_used_by_tools_cache
