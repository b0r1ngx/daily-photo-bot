"""Analytics repository. Layer: Repo (depends on: types, config)."""
from __future__ import annotations

import logging

import aiosqlite

logger = logging.getLogger(__name__)


class AnalyticsRepo:
    """Read analytics data and record API requests."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def get_total_users(self) -> int:
        """Count all registered users."""
        cursor = await self._db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_users_by_language(self) -> dict[str, int]:
        """Count users grouped by language_code."""
        cursor = await self._db.execute(
            "SELECT COALESCE(language_code, 'unknown') AS lang, COUNT(*) AS cnt "
            "FROM users GROUP BY language_code ORDER BY cnt DESC"
        )
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    async def get_active_user_count(self) -> int:
        """Count users who have at least one active schedule on an active topic."""
        cursor = await self._db.execute(
            "SELECT COUNT(DISTINCT u.id) FROM users u "
            "JOIN topics t ON t.user_id = u.id AND t.is_active = 1 "
            "JOIN schedules s ON s.topic_id = t.id AND s.is_active = 1"
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_paid_user_count(self) -> int:
        """Count users who have at least one active paid topic (is_free = 0)."""
        cursor = await self._db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM topics WHERE is_free = 0 AND is_active = 1"
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_photos_sent_since(self, since_dt_text: str) -> int:
        """Count photos sent since a given datetime (YYYY-MM-DD HH:MM:SS)."""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM sent_photos WHERE sent_at >= ?", (since_dt_text,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_api_requests_since(self, source: str, since_dt_text: str) -> int:
        """Count API requests for a given source since a given datetime (YYYY-MM-DD HH:MM:SS)."""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM api_requests WHERE source = ? AND requested_at >= ?",
            (source, since_dt_text),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def record_api_request(self, source: str) -> None:
        """Log a single external API request."""
        await self._db.execute(
            "INSERT INTO api_requests (source) VALUES (?)", (source,)
        )
        await self._db.commit()

    async def cleanup_old_api_requests(self, older_than_dt_text: str) -> int:
        """Delete api_requests older than the given datetime (YYYY-MM-DD HH:MM:SS).

        Returns count deleted.
        """
        cursor = await self._db.execute(
            "DELETE FROM api_requests WHERE requested_at < ?", (older_than_dt_text,)
        )
        await self._db.commit()
        return cursor.rowcount
