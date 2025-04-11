from unittest.mock import patch

import pytest
from litellm.types.utils import ModelResponse

from app.i18n import translate


@pytest.fixture
def isolated_cache(monkeypatch):
    cache = {}
    monkeypatch.setattr("app.i18n._translation_result_cache", cache)
    return cache


def test_translate_with_none_locale(isolated_cache):
    input_text = "Hello, world!"
    result = translate(locale=None, text=input_text)
    assert result == input_text


def test_translate_with_unsupported_locale(isolated_cache):
    input_text = "Hello, world!"
    unsupported_locale = "xx-XX"
    result = translate(unsupported_locale, input_text)
    assert result == input_text


@patch("app.i18n.call_litellm_completion")
def test_translate_with_supported_locale_no_cache(mock_completion, isolated_cache):
    input_text = "Hello, world!"
    supported_locale = "ja-JP"
    translated_text = "こんにちは、世界！"

    mock_completion.return_value = ModelResponse(
        choices=[{"message": {"content": translated_text}}]
    )

    result = translate(supported_locale, input_text)
    assert result == translated_text
    assert isolated_cache[f"Japanese:{input_text}"] == translated_text


@patch("app.i18n.call_litellm_completion")
def test_translate_with_supported_locale_cached(mock_completion, isolated_cache):
    input_text = "Hello, world!"
    supported_locale = "ja-JP"
    cached_text = "こんにちは、世界！"
    isolated_cache[f"Japanese:{input_text}"] = cached_text

    result = translate(supported_locale, input_text)
    assert result == cached_text


@patch("app.i18n.call_litellm_completion")
def test_translate_with_invalid_response(mock_completion, isolated_cache):
    input_text = "Hello, world!"
    supported_locale = "ja-JP"

    mock_completion.return_value = 123

    with pytest.raises(
        TypeError, match="Expected ModelResponse when streaming is disabled"
    ):
        translate(supported_locale, input_text)
