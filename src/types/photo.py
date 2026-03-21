"""Photo result data models. Layer: Types (zero dependencies)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhotoResult:
    """A photo fetched from an external API."""

    photo_id: str
    url: str
    photographer: str
    source_url: str
    source: str  # "pexels" or "unsplash"
    alt: str = ""
    description: str = ""  # Photographer's description (Unsplash only)
    location: str = ""  # Location string (Unsplash only)
    camera: str = ""  # Camera make/model (Unsplash only)
