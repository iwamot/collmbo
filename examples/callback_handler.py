import copy
import json
import logging

from litellm.integrations.custom_logger import CustomLogger


class CallbackHandler(CustomLogger):
    def log_pre_api_call(self, model, messages, kwargs):
        if not messages or messages[-1].get("role") != "user":
            return

        messages = [messages[-1]]
        content = messages[0].get("content")
        if isinstance(content, list):
            for c in content:
                if c["type"] == "image_url":
                    c["image_url"]["url"] = "(omitted)"
                elif c["type"] == "file":
                    c["file"]["file_data"] = "(omitted)"

        keys_to_keep = [
            "model",
            "max_tokens",
            "temperature",
            "user",
            "stream",
        ]
        model_call_dict = {
            k: copy.deepcopy(v) for k, v in kwargs.items() if k in keys_to_keep
        }
        model_call_dict["messages"] = messages

        logger = logging.getLogger("Collmbo")
        logger.info(f"model call details: {json.dumps(model_call_dict)}")

    def log_post_api_call(self, kwargs, response_obj, start_time, end_time):
        pass

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        if "complete_streaming_response" in kwargs:
            print(
                f"complete streaming response: {kwargs['complete_streaming_response']}"
            )

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        pass

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        pass

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        pass
