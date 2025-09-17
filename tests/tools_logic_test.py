import pytest

from app.tools_logic import load_classic_tools


@pytest.mark.parametrize(
    "module_name, expected",
    [
        (
            "examples.tools",
            [
                {
                    "type": "function",
                    "function": {
                        "name": "get_current_weather",
                        "description": "Get the current weather in a given location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The city and state, e.g. San Francisco, CA",
                                },
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                },
                            },
                            "required": ["location"],
                        },
                    },
                }
            ],
        ),
        (None, []),
    ],
)
def test_load_classic_tools(module_name, expected):
    result = load_classic_tools(module_name)

    assert result == expected
