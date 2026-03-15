"""Sent photo tracking repository. Layer: Repo (depends on: types, config)."""
from __future__ import annotations

import logging

import aiosqlite

logger = logging.getLogger(__name__)

# Reset sent photos when this limit is reached to allow re-sends
EXHAUSTION_THRESHOLD = 500


class SentPhotoRepo:
    """SQLite-backed sent photo tracking."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def add(self, topic_id: int, photo_id: str, source: str) -> None:
        """Record a sent photo. Ignores duplicates silently."""
        await self._db.execute(
            "INSERT OR IGNORE INTO sent_photos (topic_id, photo_id, source) VALUES (?, ?, ?)",
            (topic_id, photo_id, source),
        )
        await self._db.commit()

    async def exists(self, topic_id: int, photo_id: str, source: str) -> bool:
        """Check if a photo was already sent for a topic."""
        cursor = await self._db.execute(
            "SELECT 1 FROM sent_photos WHERE topic_id = ? AND photo_id = ? AND source = ?",
            (topic_id, photo_id, source),
        )
        row = await cursor.fetchone()
        return row is not None

    async def count_by_topic(self, topic_id: int) -> int:
        """Count total sent photos for a topic."""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM sent_photos WHERE topic_id = ?",
            (topic_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def reset_by_topic(self, topic_id: int) -> None:
        """Delete all sent photo records for a topic (when exhausted)."""
        await self._db.execute(
            "DELETE FROM sent_photos WHERE topic_id = ?",
            (topic_id,),
        )
        await self._db.commit()
        logger.info("Reset sent photos for topic_id=%d", topic_id)

    async def get_sent_ids(self, topic_id: int, source: str) -> set[str]:
        """Get all sent photo IDs for a topic from a specific source."""
        cursor = await self._db.execute(
            "SELECT photo_id FROM sent_photos WHERE topic_id = ? AND source = ?",
            (topic_id, source),
        )
        rows = await cursor.fetchall()
        return {row[0] for row in rows}
