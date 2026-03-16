"""Internationalization support — translation function. Layer: Config (depends on: types only)."""

import json
import logging
from pathlib import Path
from typing import Any

from src.types.i18n import MessageKey, SupportedLanguage

logger = logging.getLogger(__name__)

_TRANSLATIONS_DIR = Path(__file__).resolve().parent / "translations"
_translations_cache: dict[str, dict[str, str]] = {}
_DEFAULT_LANG = SupportedLanguage.EN.value
_SUPPORTED_LANGS: frozenset[str] = frozenset(lang.value for lang in SupportedLanguage)


def _load_translations(lang: str) -> dict[str, str]:
    """Load translation file for a language. Cached after first load."""
    if lang in _translations_cache:
        return _translations_cache[lang]

    path = _TRANSLATIONS_DIR / f"{lang}.json"
    if not path.exists():
        logger.warning("Translation file not found: %s", path)
        return {}

    with open(path, encoding="utf-8") as f:
        data: dict[str, str] = json.load(f)

    _translations_cache[lang] = data
    return data


def _resolve_language(language_code: str | None) -> str:
    """Resolve a Telegram language_code to a supported language."""
    if not language_code:
        return _DEFAULT_LANG

    base = language_code.split("-")[0].lower()

    if base in _SUPPORTED_LANGS:
        return base
    return _DEFAULT_LANG


def t(key: MessageKey, language_code: str | None = None, **kwargs: Any) -> str:
    """Get translated string by key.

    Falls back to English if key not found in target language.
    Supports string formatting with **kwargs.
    """
    lang = _resolve_language(language_code)

    # Try target language first
    translations = _load_translations(lang)
    text = translations.get(key)

    # Fallback to English
    if text is None and lang != _DEFAULT_LANG:
        translations = _load_translations(_DEFAULT_LANG)
        text = translations.get(key)

    # Final fallback: return the key itself
    if text is None:
        logger.warning("Missing translation: key=%s, lang=%s", key, lang)
        return key

    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError as exc:
            logger.warning(
                "Translation format error: key=%s, lang=%s, error=%s", key, lang, exc
            )
            return text

    return text
