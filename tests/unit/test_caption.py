"""Unit tests for build_photo_caption."""
from __future__ import annotations

from src.runtime.caption import build_photo_caption
from src.types.photo import PhotoResult
from src.types.user import MetadataPrefs


def _make_photo(**kwargs) -> PhotoResult:
    """Helper to build a PhotoResult with defaults."""
    defaults = {
        "photo_id": "abc123",
        "url": "https://images.unsplash.com/abc.jpg",
        "photographer": "Test Photographer",
        "source_url": "https://unsplash.com/photos/abc",
        "source": "unsplash",
        "alt": "A parrot",
        "description": "Colorful macaw in the wild",
        "location": "Montreal, Canada",
        "camera": "Canon, EOS 40D",
    }
    defaults.update(kwargs)
    return PhotoResult(**defaults)


def test_all_metadata_on_with_data():
    """When all prefs ON and metadata present, all lines appear."""
    photo = _make_photo()
    prefs = MetadataPrefs(show_description=True, show_location=True, show_camera=True)

    caption = build_photo_caption(photo, "parrots", "en", prefs)

    assert "parrots" in caption
    assert "Test Photographer" in caption
    assert "Colorful macaw in the wild" in caption
    assert "Montreal" in caption
    assert "Canon" in caption


def test_all_metadata_off():
    """When all prefs OFF, no metadata lines appear."""
    photo = _make_photo()
    prefs = MetadataPrefs(show_description=False, show_location=False, show_camera=False)

    caption = build_photo_caption(photo, "parrots", "en", prefs)

    assert "parrots" in caption
    assert "Test Photographer" in caption
    # No metadata lines
    assert "Colorful macaw" not in caption
    assert "Montreal" not in caption
    assert "Canon" not in caption


def test_partial_metadata():
    """Only enabled metadata fields appear in caption."""
    photo = _make_photo()
    prefs = MetadataPrefs(show_description=True, show_location=False, show_camera=True)

    caption = build_photo_caption(photo, "parrots", "en", prefs)

    assert "Colorful macaw" in caption
    assert "Montreal" not in caption
    assert "Canon" in caption


def test_empty_metadata_shows_not_specified():
    """When pref ON but value empty, 'not specified' fallback appears."""
    photo = _make_photo(description="", location="", camera="")
    prefs = MetadataPrefs(show_description=True, show_location=True, show_camera=True)

    caption = build_photo_caption(photo, "parrots", "en", prefs)

    # The "not specified by author" text should appear (escaped)
    assert "not specified" in caption


def test_markdown_special_chars_escaped():
    """Special MarkdownV2 characters in metadata are properly escaped."""
    photo = _make_photo(
        description="A *bold* photo with (parentheses)",
        photographer="Jane. Doe",
    )
    prefs = MetadataPrefs(show_description=True, show_location=False, show_camera=False)

    caption = build_photo_caption(photo, "parrots", "en", prefs)

    # Should contain escaped versions, not raw markdown
    assert "\\*bold\\*" in caption
    assert "Jane\\. Doe" in caption
