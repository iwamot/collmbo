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
    result = translate(locale=unsupported_locale, text=input_text)
    assert result == input_text


def test_translate_with_supported_locale_no_cache(isolated_cache):
    input_text = "Hello, world!"
    supported_locale = "ja-JP"
    translated_text = "こんにちは、世界！"

    def mock_completion_fn(*args, **kwargs):
        return ModelResponse(choices=[{"message": {"content": translated_text}}])

    result = translate(
        locale=supported_locale, text=input_text, completion_fn=mock_completion_fn
    )
    assert result == translated_text
    assert isolated_cache[f"Japanese:{input_text}"] == translated_text


def test_translate_with_supported_locale_cached(isolated_cache):
    input_text = "Hello, world!"
    supported_locale = "ja-JP"
    cached_text = "こんにちは、世界！"
    isolated_cache[f"Japanese:{input_text}"] = cached_text

    def mock_completion_fn(*args, **kwargs):
        raise RuntimeError("This should not be called")

    result = translate(
        locale=supported_locale, text=input_text, completion_fn=mock_completion_fn
    )
    assert result == cached_text


def test_translate_with_invalid_response(isolated_cache):
    input_text = "Hello, world!"
    supported_locale = "ja-JP"

    def mock_completion_fn(*args, **kwargs):
        return 123

    with pytest.raises(
        TypeError, match="Expected ModelResponse when streaming is disabled"
    ):
        translate(
            locale=supported_locale, text=input_text, completion_fn=mock_completion_fn
        )
