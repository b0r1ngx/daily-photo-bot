"""Topic repository. Layer: Repo (depends on: types, config)."""
from __future__ import annotations

import logging

import aiosqlite

from src.types.user import Topic

logger = logging.getLogger(__name__)


class TopicRepo:
    """SQLite-backed topic data access."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def create(self, user_id: int, name: str, is_free: bool = True) -> Topic:
        """Create a new topic for a user."""
        cursor = await self._db.execute(
            "INSERT INTO topics (user_id, name, is_free) VALUES (?, ?, ?)",
            (user_id, name, int(is_free)),
        )
        await self._db.commit()
        logger.info("Created topic '%s' for user_id=%d (free=%s)", name, user_id, is_free)
        return Topic(
            id=cursor.lastrowid,
            user_id=user_id,
            name=name,
            is_free=is_free,
            is_active=True,
        )

    async def get_by_id(self, topic_id: int) -> Topic | None:
        """Get a single active topic by ID."""
        cursor = await self._db.execute(
            'SELECT id, user_id, name, is_free, is_active, created_at '
            'FROM topics WHERE id = ? AND is_active = 1',
            (topic_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_topic(row) if row else None

    async def get_by_user(self, user_id: int, active_only: bool = True) -> list[Topic]:
        """Get all topics for a user."""
        query = (
            "SELECT id, user_id, name, is_free, is_active, created_at "
            "FROM topics WHERE user_id = ?"
        )
        params: list[int] = [user_id]
        if active_only:
            query += " AND is_active = 1"
        cursor = await self._db.execute(query, params)
        rows = await cursor.fetchall()
        return [self._row_to_topic(row) for row in rows]

    async def count_by_user(self, user_id: int) -> int:
        """Count active topics for a user."""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM topics WHERE user_id = ? AND is_active = 1",
            (user_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def delete(self, topic_id: int) -> None:
        """Soft-delete a topic (set is_active = 0)."""
        await self._db.execute(
            "UPDATE topics SET is_active = 0 WHERE id = ?",
            (topic_id,),
        )
        await self._db.commit()
        logger.info("Deactivated topic_id=%d", topic_id)

    async def update_name(self, topic_id: int, new_name: str) -> None:
        """Rename an active topic."""
        cursor = await self._db.execute(
            'UPDATE topics SET name = ? WHERE id = ? AND is_active = 1',
            (new_name, topic_id),
        )
        await self._db.commit()
        if cursor.rowcount == 0:
            raise ValueError(f'Topic {topic_id} not found or inactive')
        logger.info("Renamed topic_id=%d to '%s'", topic_id, new_name)

    async def get_by_id_with_user_language(
        self, topic_id: int,
    ) -> tuple[str, str | None] | None:
        """Get topic name and owner's language_code for an active topic.

        Returns:
            Tuple of (topic_name, language_code) or None if not found/inactive.
        """
        cursor = await self._db.execute(
            "SELECT t.name, u.language_code "
            "FROM topics t "
            "JOIN users u ON t.user_id = u.id "
            "WHERE t.id = ? AND t.is_active = 1",
            (topic_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return (row[0], row[1])

    async def get_owner_telegram_id(self, topic_id: int) -> int | None:
        """Get the Telegram user ID of the topic owner."""
        cursor = await self._db.execute(
            "SELECT u.telegram_id FROM users u "
            "JOIN topics t ON t.user_id = u.id "
            "WHERE t.id = ? AND t.is_active = 1",
            (topic_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    def _row_to_topic(row: aiosqlite.Row) -> Topic:
        return Topic(
            id=row[0],
            user_id=row[1],
            name=row[2],
            is_free=bool(row[3]),
            is_active=bool(row[4]),
            created_at=row[5],
        )
