from typing import Optional

from litellm.types.utils import ModelResponse

from app.litellm_ops import call_litellm_completion

# https://slack.com/help/articles/215058658-Manage-your-language-preferences
_locale_to_lang = {
    "en-US": "English",
    "en-GB": "English",
    "de-DE": "German",
    "es-ES": "Spanish",
    "es-LA": "Spanish",
    "fr-FR": "French",
    "it-IT": "Italian",
    "pt-BR": "Portuguese",
    "ja-JP": "Japanese",
    "zh-CN": "Chinese",
    "zh-TW": "Chinese",
    "ko-KR": "Korean",
}


def from_locale_to_lang(locale: Optional[str]) -> Optional[str]:
    return None if locale is None else _locale_to_lang.get(locale)


_translation_result_cache: dict[str, str] = {}


def translate(*, locale: Optional[str], text: str) -> str:
    lang = from_locale_to_lang(locale)
    if lang is None or lang == "English":
        return text

    cached_result = _translation_result_cache.get(f"{lang}:{text}")
    if cached_result is not None:
        return cached_result
    response = call_litellm_completion(
        messages=[
            {
                "role": "system",
                "content": "You're the AI model that primarily focuses on the quality of language translation. "
                "You always respond with the only the translated text in a format suitable for Slack user interface. "
                "Slack's emoji (e.g., :hourglass_flowing_sand:) and mention parts must be kept as-is. "
                "You don't change the meaning of sentences when translating them into a different language. "
                "When the given text is a single verb/noun, its translated text must be a norm/verb form too. "
                "When the given text is in markdown format, the format must be kept as much as possible. ",
            },
            {
                "role": "user",
                "content": f"Can you translate the following text into {lang} in a professional tone? "
                "Your response must omit any English version / pronunciation guide for the result. "
                "Again, no need to append any English notes and guides about the result. "
                "Just return the translation result. "
                f"Here is the original sentence you need to translate:\n{text}",
            },
        ],
        temperature=1,
        user="system",
    )
    if not isinstance(response, ModelResponse):
        raise TypeError("Expected ModelResponse when streaming is disabled")
    translated_text = response["choices"][0]["message"].get("content")
    _translation_result_cache[f"{lang}:{text}"] = translated_text
    return translated_text
