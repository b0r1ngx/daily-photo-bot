"""Tests for internationalization."""

import pytest

from src.config.i18n import _resolve_language, t


def test_t_english_default():
    """English text returned by default."""
    result = t("action_cancelled")
    assert "↩️" in result
    assert "cancelled" in result.lower()


def test_t_russian():
    """Russian translation returned for Russian language code."""
    result = t("action_cancelled", "ru")
    assert result != t("action_cancelled", "en")


def test_t_spanish():
    """Spanish translation returned for Spanish language code."""
    result = t("action_cancelled", "es")
    assert result != t("action_cancelled", "en")


def test_t_portuguese():
    """Portuguese translation returned for Portuguese language code."""
    result = t("action_cancelled", "pt")
    assert result != t("action_cancelled", "en")


def test_t_chinese():
    """Chinese translation returned for Chinese language code."""
    result = t("action_cancelled", "zh")
    assert result != t("action_cancelled", "en")


def test_t_hindi():
    """Hindi translation returned for Hindi language code."""
    result = t("action_cancelled", "hi")
    assert result != t("action_cancelled", "en")


def test_t_arabic():
    """Arabic translation returned for Arabic language code."""
    result = t("action_cancelled", "ar")
    assert result != t("action_cancelled", "en")


def test_t_malay():
    """Malay translation returned for Malay language code."""
    result = t("action_cancelled", "ms")
    assert result != t("action_cancelled", "en")


def test_t_bengali():
    """Bengali translation returned for Bengali language code."""
    result = t("action_cancelled", "bn")
    assert result != t("action_cancelled", "en")


def test_t_french():
    """French translation returned for French language code."""
    result = t("action_cancelled", "fr")
    assert result != t("action_cancelled", "en")


def test_t_italian():
    """Italian translation returned for Italian language code."""
    result = t("action_cancelled", "it")
    assert result != t("action_cancelled", "en")


def test_t_german():
    """German translation returned for German language code."""
    result = t("action_cancelled", "de")
    assert result != t("action_cancelled", "en")


def test_t_with_kwargs():
    """Format placeholders are filled."""
    result = t("version_text", "en", version="1.0")
    assert "1.0" in result


def test_t_with_kwargs_all_languages():
    """Format placeholders work in all languages."""
    for lang in ("en", "es", "ru", "pt", "zh", "hi", "ar", "ms", "bn", "fr", "it", "de"):
        result = t("version_text", lang, version="2.5")
        assert "2.5" in result


def test_t_fallback_to_english():
    """Unknown language falls back to English."""
    en_result = t("action_cancelled", "en")
    unknown_result = t("action_cancelled", "ja")  # Japanese not supported
    assert en_result == unknown_result


def test_t_missing_key():
    """Missing key returns the key itself."""
    result = t("nonexistent_key_xyz", "en")  # type: ignore[arg-type]
    assert result == "nonexistent_key_xyz"


def test_t_none_language():
    """None language defaults to English."""
    en_result = t("action_cancelled", "en")
    none_result = t("action_cancelled", None)
    assert en_result == none_result


def test_resolve_language_none():
    """None language resolves to English."""
    assert _resolve_language(None) == "en"


def test_resolve_language_with_region():
    """Language code with region uses base."""
    assert _resolve_language("pt-BR") == "pt"
    assert _resolve_language("zh-CN") == "zh"
    assert _resolve_language("en-US") == "en"


def test_resolve_language_supported():
    """All supported languages resolve correctly."""
    assert _resolve_language("en") == "en"
    assert _resolve_language("es") == "es"
    assert _resolve_language("ru") == "ru"
    assert _resolve_language("pt") == "pt"
    assert _resolve_language("zh") == "zh"
    assert _resolve_language("hi") == "hi"
    assert _resolve_language("ar") == "ar"
    assert _resolve_language("ms") == "ms"
    assert _resolve_language("bn") == "bn"
    assert _resolve_language("fr") == "fr"
    assert _resolve_language("it") == "it"
    assert _resolve_language("de") == "de"


def test_resolve_language_unsupported():
    """Unsupported language falls back to English."""
    assert _resolve_language("ja") == "en"
    assert _resolve_language("ko") == "en"
    assert _resolve_language("sv") == "en"


@pytest.mark.parametrize("lang", ["en", "es", "ru", "pt", "zh", "hi", "ar", "ms", "bn", "fr", "it", "de"])
def test_all_message_keys_present(lang: str):
    """Every language file contains all required keys."""
    # Test a representative set of keys across all languages
    keys = [
        "welcome_back",
        "welcome_new",
        "use_start_first",
        "error_try_again",
        "help_text",
        "action_cancelled",
        "unknown_message",
        "enter_new_topic",
        "topic_added",
        "no_topics",
        "topic_deleted",
        "schedule_removed",
        "photo_caption",
        "payment_failed",
        "payment_success",
    ]
    for key in keys:
        result = t(key, lang)  # type: ignore[arg-type]
        assert result != key, f"Key '{key}' missing in {lang}.json"
