import copy
import json
import logging

from litellm.integrations.custom_logger import CustomLogger


class CallbackHandler(CustomLogger):
    def log_pre_api_call(self, model, messages, kwargs):
        # Omit image data and output request log
        keys_to_keep = [
            "model",
            "messages",
            "max_tokens",
            "temperature",
            "user",
            "stream",
            "tools",
        ]
        model_call_dict = {
            k: copy.deepcopy(v) for k, v in kwargs.items() if k in keys_to_keep
        }
        if "messages" in model_call_dict:
            for message in model_call_dict["messages"]:
                if "content" in message and isinstance(message["content"], list):
                    for content in message["content"]:
                        if content["type"] == "image_url":
                            content["image_url"]["url"] = "(omitted)"
        logger = logging.getLogger("Collmbo")
        logger.info(f"model call details: {json.dumps(model_call_dict)}")

    def log_post_api_call(self, kwargs, response_obj, start_time, end_time):
        pass

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        pass

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        pass

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        pass

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        pass
