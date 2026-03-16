"""Photo fetching service. Layer: Service (depends on: types, config).

Fetches photos from Pexels (primary) and Unsplash (fallback).
Uses dependency injection for the sent photo repository.
"""
from __future__ import annotations

import logging
import random

import httpx

from src.config.constants import (
    PEXELS_MAX_PAGE,
    PEXELS_PER_PAGE,
    PEXELS_SEARCH_URL,
    PHOTO_REQUEST_TIMEOUT,
    UNSPLASH_COUNT,
    UNSPLASH_RANDOM_URL,
)
from src.config.settings import PEXELS_API_KEY, UNSPLASH_ACCESS_KEY
from src.types.exceptions import PhotoNotFoundError, PhotoSourceError, RateLimitError
from src.types.photo import PhotoResult
from src.types.protocols import SentPhotoRepository

logger = logging.getLogger(__name__)

# Reset threshold — when all photos for a topic have been exhausted
_EXHAUSTION_RESET_THRESHOLD = 500


class PhotoService:
    """Fetches unique photos from external APIs."""

    def __init__(self, sent_photo_repo: SentPhotoRepository) -> None:
        self._sent_repo = sent_photo_repo

    async def get_photo(self, topic: str, topic_id: int) -> PhotoResult:
        """Get a unique photo for a topic. Tries Pexels first, then Unsplash.

        Args:
            topic: The search keyword (e.g., "parrots").
            topic_id: Database topic ID for dedup tracking.

        Returns:
            PhotoResult with URL and attribution.

        Raises:
            PhotoNotFoundError: If no photos found for the topic.
            PhotoSourceError: If all APIs fail.
        """
        # Check if we need to reset (photo exhaustion)
        sent_count = await self._sent_repo.count_by_topic(topic_id)
        if sent_count >= _EXHAUSTION_RESET_THRESHOLD:
            logger.info(
                "Photo exhaustion for topic_id=%d (%d sent), resetting.",
                topic_id,
                sent_count,
            )
            await self._sent_repo.reset_by_topic(topic_id)

        # Try Pexels first
        try:
            result = await self._fetch_from_pexels(topic, topic_id)
            if result:
                await self._sent_repo.add(topic_id, result.photo_id, result.source)
                return result
        except RateLimitError:
            logger.warning("Pexels rate limit hit, falling back to Unsplash.")
        except PhotoSourceError as exc:
            logger.warning("Pexels error: %s, falling back to Unsplash.", exc)

        # Fallback to Unsplash
        if UNSPLASH_ACCESS_KEY:
            try:
                result = await self._fetch_from_unsplash(topic, topic_id)
                if result:
                    await self._sent_repo.add(topic_id, result.photo_id, result.source)
                    return result
            except PhotoSourceError as exc:
                logger.warning("Unsplash also failed: %s", exc)

        raise PhotoNotFoundError(topic)

    async def _fetch_from_pexels(self, topic: str, topic_id: int) -> PhotoResult | None:
        """Fetch a random unsent photo from Pexels."""
        sent_ids = await self._sent_repo.get_sent_ids(topic_id, "pexels")
        page = random.randint(1, PEXELS_MAX_PAGE)

        async with httpx.AsyncClient(timeout=PHOTO_REQUEST_TIMEOUT) as client:
            response = await client.get(
                PEXELS_SEARCH_URL,
                headers={"Authorization": PEXELS_API_KEY},
                params={
                    "query": topic,
                    "per_page": PEXELS_PER_PAGE,
                    "page": page,
                    "orientation": "landscape",
                },
            )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError("pexels", retry_after)

        if response.status_code != 200:
            raise PhotoSourceError(f"Pexels API returned {response.status_code}")

        data = response.json()
        photos = data.get("photos", [])

        if not photos:
            return None

        # Filter out already-sent photos
        unsent = [p for p in photos if str(p["id"]) not in sent_ids]

        if not unsent:
            # All photos on this page already sent — try different page
            alt_page = random.choice([p for p in range(1, PEXELS_MAX_PAGE + 1) if p != page])
            async with httpx.AsyncClient(timeout=PHOTO_REQUEST_TIMEOUT) as client:
                response = await client.get(
                    PEXELS_SEARCH_URL,
                    headers={"Authorization": PEXELS_API_KEY},
                    params={
                        "query": topic,
                        "per_page": PEXELS_PER_PAGE,
                        "page": alt_page,
                        "orientation": "landscape",
                    },
                )
            if response.status_code == 200:
                photos = response.json().get("photos", [])
                unsent = [p for p in photos if str(p["id"]) not in sent_ids]

        if not unsent:
            return None

        photo = random.choice(unsent)
        return PhotoResult(
            photo_id=str(photo["id"]),
            url=photo["src"]["large"],
            photographer=photo["photographer"],
            source_url=photo["url"],
            source="pexels",
            alt=photo.get("alt", topic),
        )

    async def _fetch_from_unsplash(self, topic: str, topic_id: int) -> PhotoResult | None:
        """Fetch a random unsent photo from Unsplash."""
        sent_ids = await self._sent_repo.get_sent_ids(topic_id, "unsplash")

        async with httpx.AsyncClient(timeout=PHOTO_REQUEST_TIMEOUT) as client:
            response = await client.get(
                UNSPLASH_RANDOM_URL,
                headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                params={
                    "query": topic,
                    "count": UNSPLASH_COUNT,
                    "orientation": "landscape",
                },
            )

        if response.status_code == 429:
            raise RateLimitError("unsplash")

        if response.status_code == 403:
            raise RateLimitError("unsplash")

        if response.status_code != 200:
            raise PhotoSourceError(f"Unsplash API returned {response.status_code}")

        photos = response.json()
        if not isinstance(photos, list):
            photos = [photos]

        unsent = [p for p in photos if str(p["id"]) not in sent_ids]

        if not unsent:
            return None

        photo = random.choice(unsent)

        # Track download (Unsplash ToS requirement)
        download_url = photo.get("links", {}).get("download_location")
        if download_url:
            try:
                async with httpx.AsyncClient(timeout=5) as dl_client:
                    await dl_client.get(
                        download_url,
                        headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                    )
            except httpx.HTTPError:
                pass  # Non-critical: tracking failure shouldn't block photo send

        return PhotoResult(
            photo_id=str(photo["id"]),
            url=photo["urls"]["regular"],
            photographer=photo["user"]["name"],
            source_url=photo["links"]["html"],
            source="unsplash",
            alt=photo.get("alt_description", topic) or topic,
        )
