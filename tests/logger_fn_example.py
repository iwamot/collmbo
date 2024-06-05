import copy
import json


def logger_fn(model_call_dict):
    keys_to_keep = [
        "model",
        "messages",
        "max_tokens",
        "temperature",
        "user",
        "stream",
        "tools",
    ]
    log_data = {
        k: copy.deepcopy(v) for k, v in model_call_dict.items() if k in keys_to_keep
    }
    if "messages" in log_data:
        for message in log_data["messages"]:
            if "content" in message and isinstance(message["content"], list):
                for content in message["content"]:
                    if content["type"] == "image_url":
                        content["image_url"]["url"] = "(omitted)"
    print("model call details:", json.dumps(log_data))
