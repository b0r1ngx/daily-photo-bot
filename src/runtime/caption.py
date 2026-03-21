"""Photo caption builder. Layer: Runtime (depends on: types, config)."""
from __future__ import annotations

from telegram.helpers import escape_markdown

from src.config.i18n import t
from src.types.photo import PhotoResult
from src.types.user import MetadataPrefs


def build_photo_caption(
    photo: PhotoResult,
    topic_name: str,
    language_code: str | None,
    prefs: MetadataPrefs,
) -> str:
    """Build a MarkdownV2-escaped caption with optional metadata lines.

    Args:
        photo: The fetched photo result with attribution and metadata.
        topic_name: Display name for the topic.
        language_code: User's language code for i18n.
        prefs: Per-topic metadata display preferences.

    Returns:
        Complete MarkdownV2 caption string.
    """
    photographer = escape_markdown(photo.photographer, version=2)
    source_display = escape_markdown(photo.source.title(), version=2)
    url_safe = photo.source_url.replace("\\", "\\\\").replace(")", "\\)")
    source_with_link = f"[{source_display}]({url_safe})"

    caption = t(
        "photo_caption",
        language_code,
        name=escape_markdown(topic_name, version=2),
        photographer=photographer,
        source=source_with_link,
    )

    # Append metadata lines based on preferences
    not_specified = escape_markdown(
        t("metadata_not_specified", language_code), version=2,
    )

    if prefs.show_description:
        label = t("metadata_description", language_code)
        if photo.description:
            value = escape_markdown(photo.description, version=2)
        else:
            value = not_specified
        caption += f"\n\U0001f4dd {escape_markdown(label, version=2)}: {value}"

    if prefs.show_location:
        label = t("metadata_location", language_code)
        if photo.location:
            value = escape_markdown(photo.location, version=2)
        else:
            value = not_specified
        caption += f"\n\U0001f4cd {escape_markdown(label, version=2)}: {value}"

    if prefs.show_camera:
        label = t("metadata_camera", language_code)
        if photo.camera:
            value = escape_markdown(photo.camera, version=2)
        else:
            value = not_specified
        caption += f"\n\U0001f4f7 {escape_markdown(label, version=2)}: {value}"

    return caption
