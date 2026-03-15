"""Unit tests for _enrich_query search term enrichment."""
from __future__ import annotations

from src.service.photo_service import _enrich_query


def test_enrich_query_english_passthrough():
    """English topics pass through unchanged."""
    assert _enrich_query("sunset", "en") == "sunset"
    assert _enrich_query("sunset", "en-US") == "sunset"


def test_enrich_query_none_language():
    """None language passes through."""
    assert _enrich_query("кот", None) == "кот"


def test_enrich_query_russian_single_word():
    """Known Russian words are translated."""
    assert _enrich_query("кот", "ru") == "cat"


def test_enrich_query_russian_unknown_word():
    """Unknown Russian words pass through."""
    assert _enrich_query("самовар", "ru") == "самовар"


def test_enrich_query_multi_word_partial():
    """Multi-word topics: known words translated, unknown kept."""
    result = _enrich_query("красивый кот", "ru")
    assert "cat" in result
    assert "красивый" in result


def test_enrich_query_spanish():
    """Spanish words translate correctly."""
    assert _enrich_query("gato", "es") == "cat"


def test_enrich_query_unknown_language():
    """Unknown language codes pass through."""
    assert _enrich_query("кот", "ja") == "кот"


def test_enrich_query_full_topic_match():
    """Full topic matched as single term."""
    assert _enrich_query("горы", "ru") == "mountains"


def test_enrich_query_language_with_region():
    """Language codes with region (pt-BR) use base code."""
    assert _enrich_query("gato", "pt-BR") == "cat"
