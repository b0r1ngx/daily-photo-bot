"""Schedule repository. Layer: Repo (depends on: types, config)."""
from __future__ import annotations

import logging

import aiosqlite

from src.types.schedule import ScheduleConfig, ScheduleType

logger = logging.getLogger(__name__)


class ScheduleRepo:
    """SQLite-backed schedule data access."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def create_or_update(
        self, topic_id: int, schedule_type: str, value: str
    ) -> ScheduleConfig:
        """Create or update schedule for a topic (UPSERT)."""
        await self._db.execute(
            """
            INSERT INTO schedules (topic_id, schedule_type, value)
            VALUES (?, ?, ?)
            ON CONFLICT(topic_id) DO UPDATE SET
                schedule_type = excluded.schedule_type,
                value = excluded.value,
                is_active = 1
            """,
            (topic_id, schedule_type, value),
        )
        await self._db.commit()
        logger.info(
            "Upserted schedule for topic_id=%d: type=%s, value=%s",
            topic_id,
            schedule_type,
            value,
        )
        result = await self.get_by_topic(topic_id)
        return result  # type: ignore[return-value]

    async def get_by_topic(self, topic_id: int) -> ScheduleConfig | None:
        """Get schedule for a specific topic."""
        cursor = await self._db.execute(
            "SELECT id, topic_id, schedule_type, value, is_active, last_sent_at "
            "FROM schedules WHERE topic_id = ?",
            (topic_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_config(row)

    async def get_all_active(self) -> list[ScheduleConfig]:
        """Get all active schedules (for startup reload)."""
        cursor = await self._db.execute(
            "SELECT id, topic_id, schedule_type, value, is_active, last_sent_at "
            "FROM schedules WHERE is_active = 1"
        )
        rows = await cursor.fetchall()
        return [self._row_to_config(row) for row in rows]

    async def update_last_sent(self, schedule_id: int) -> None:
        """Update last_sent_at timestamp for a schedule."""
        await self._db.execute(
            "UPDATE schedules SET last_sent_at = datetime('now') WHERE id = ?",
            (schedule_id,),
        )
        await self._db.commit()

    async def delete_by_topic(self, topic_id: int) -> None:
        """Deactivate schedule for a topic."""
        await self._db.execute(
            "UPDATE schedules SET is_active = 0 WHERE topic_id = ?",
            (topic_id,),
        )
        await self._db.commit()
        logger.info("Deactivated schedule for topic_id=%d", topic_id)

    @staticmethod
    def _row_to_config(row: aiosqlite.Row) -> ScheduleConfig:
        return ScheduleConfig(
            id=row[0],
            topic_id=row[1],
            schedule_type=ScheduleType(row[2]),
            value=row[3],
            is_active=bool(row[4]),
            last_sent_at=row[5],
        )
