"""Share repository. Layer: Repo (depends on: types, config)."""
from __future__ import annotations

import logging

import aiosqlite

from src.types.share import TopicSubscription

logger = logging.getLogger(__name__)


class ShareRepo:
    """SQLite-backed topic sharing data access."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def get_share_token(self, topic_id: int) -> str | None:
        """Get the share token for a topic, or None if not set."""
        cursor = await self._db.execute(
            "SELECT share_token FROM topics WHERE id = ? AND is_active = 1",
            (topic_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    async def set_share_token(self, topic_id: int, token: str) -> None:
        """Set/update the share token for a topic."""
        cursor = await self._db.execute(
            "UPDATE topics SET share_token = ? WHERE id = ? AND is_active = 1",
            (token, topic_id),
        )
        await self._db.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"Topic {topic_id} not found or inactive")

    async def get_topic_id_by_share_token(self, token: str) -> int | None:
        """Look up the active topic ID for a given share token."""
        cursor = await self._db.execute(
            "SELECT id FROM topics WHERE share_token = ? AND is_active = 1",
            (token,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    async def create_subscription(
        self, topic_id: int, subscriber_user_id: int,
    ) -> TopicSubscription:
        """Create a new subscription or reactivate a soft-deleted one."""
        # Check for existing soft-deleted subscription to reactivate
        cursor = await self._db.execute(
            "SELECT id FROM topic_subscriptions "
            "WHERE topic_id = ? AND subscriber_user_id = ? AND is_active = 0",
            (topic_id, subscriber_user_id),
        )
        existing = await cursor.fetchone()

        if existing:
            await self._db.execute(
                "UPDATE topic_subscriptions SET is_active = 1 WHERE id = ?",
                (existing[0],),
            )
            await self._db.commit()
            logger.info(
                "Reactivated subscription id=%d for topic_id=%d, user_id=%d",
                existing[0], topic_id, subscriber_user_id,
            )
            return TopicSubscription(
                id=existing[0],
                topic_id=topic_id,
                subscriber_user_id=subscriber_user_id,
                is_active=True,
            )

        cursor = await self._db.execute(
            "INSERT INTO topic_subscriptions (topic_id, subscriber_user_id) VALUES (?, ?)",
            (topic_id, subscriber_user_id),
        )
        await self._db.commit()
        logger.info(
            "Created subscription for topic_id=%d, subscriber_user_id=%d",
            topic_id, subscriber_user_id,
        )
        return TopicSubscription(
            id=cursor.lastrowid,
            topic_id=topic_id,
            subscriber_user_id=subscriber_user_id,
            is_active=True,
        )

    async def deactivate_subscription(
        self, topic_id: int, subscriber_user_id: int,
    ) -> bool:
        """Soft-delete a subscription. Returns True if a row was updated."""
        cursor = await self._db.execute(
            "UPDATE topic_subscriptions SET is_active = 0 "
            "WHERE topic_id = ? AND subscriber_user_id = ? AND is_active = 1",
            (topic_id, subscriber_user_id),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def get_active_subscription_count(self, topic_id: int) -> int:
        """Count active subscribers for a topic."""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM topic_subscriptions "
            "WHERE topic_id = ? AND is_active = 1",
            (topic_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_subscription(
        self, topic_id: int, subscriber_user_id: int,
    ) -> TopicSubscription | None:
        """Get a subscription by topic and subscriber."""
        cursor = await self._db.execute(
            "SELECT id, topic_id, subscriber_user_id, is_active, created_at "
            "FROM topic_subscriptions "
            "WHERE topic_id = ? AND subscriber_user_id = ?",
            (topic_id, subscriber_user_id),
        )
        row = await cursor.fetchone()
        return self._row_to_subscription(row) if row else None

    async def get_subscriber_telegram_ids(self, topic_id: int) -> list[int]:
        """Get Telegram IDs of all active subscribers for fan-out delivery."""
        cursor = await self._db.execute(
            "SELECT u.telegram_id FROM users u "
            "JOIN topic_subscriptions ts ON ts.subscriber_user_id = u.id "
            "WHERE ts.topic_id = ? AND ts.is_active = 1",
            (topic_id,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    @staticmethod
    def _row_to_subscription(row: aiosqlite.Row) -> TopicSubscription:
        return TopicSubscription(
            id=row[0],
            topic_id=row[1],
            subscriber_user_id=row[2],
            is_active=bool(row[3]),
            created_at=row[4],
        )
